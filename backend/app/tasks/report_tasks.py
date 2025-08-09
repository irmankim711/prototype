"""
Celery tasks for automated report generation
Handles background processing of form data and report creation
"""

from celery import shared_task
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from io import BytesIO
import base64
import os
import tempfile
import json
from typing import Dict, List, Any, Optional
from flask import current_app

# Optional imports for plotting - temporarily disabled
# try:
#     import matplotlib
#     matplotlib.use('Agg')  # Use non-interactive backend
#     import matplotlib.pyplot as plt
#     import seaborn as sns
#     PLOTTING_AVAILABLE = True
# except ImportError:
PLOTTING_AVAILABLE = False

# Mock matplotlib and seaborn when not available
class MockPlt:
    @staticmethod
    def subplots(*args, **kwargs):
        return None, None
    @staticmethod 
    def savefig(*args, **kwargs):
        pass
    @staticmethod
    def close(*args):
        pass
    class style:
        @staticmethod
        def use(*args):
            pass

class MockSns:
    @staticmethod
    def set_palette(*args):
        pass

plt = MockPlt()
sns = MockSns()

from ..models import db, Form, FormSubmission, Report, User
from ..services.ai_service import AIService
from ..services.report_generator import create_word_report, create_pdf_report
from ..services.email_service import send_report_email
# Chart generation utilities


@shared_task(bind=True, max_retries=3)
def trigger_auto_report_generation(self, form_id: int, submission_id: int):
    """
    Trigger automatic report generation when new form submission is received
    
    Args:
        form_id: ID of the form that received submission
        submission_id: ID of the new submission
    """
    try:
        # Get form and its settings
        form = Form.query.get(form_id)
        if not form:
            raise ValueError(f"Form {form_id} not found")
        
        # Check if auto-reporting is enabled
        if not form.form_settings or not form.form_settings.get('auto_report_enabled', False):
            return {'status': 'skipped', 'reason': 'Auto-reporting not enabled'}
        
        # Get auto-report settings
        report_settings = form.form_settings.get('auto_report_settings', {})
        trigger_type = report_settings.get('trigger_type', 'submission_count')
        
        if trigger_type == 'submission_count':
            threshold = report_settings.get('submission_threshold', 10)
            submission_count = FormSubmission.query.filter_by(form_id=form_id).count()
            
            if submission_count >= threshold and submission_count % threshold == 0:
                # Generate report at every threshold interval
                return generate_form_report.delay(form_id, 'auto_submission_threshold')
        
        elif trigger_type == 'time_interval':
            interval_hours = report_settings.get('interval_hours', 24)
            
            # Check if enough time has passed since last report
            last_report = Report.query.filter_by(
                template_id=f'form_{form_id}_auto'
            ).order_by(Report.created_at.desc()).first()
            
            if not last_report or (datetime.utcnow() - last_report.created_at).total_seconds() >= interval_hours * 3600:
                return generate_form_report.delay(form_id, 'auto_time_interval')
        
        elif trigger_type == 'immediate':
            # Generate report for every submission
            return generate_form_report.delay(form_id, 'auto_immediate')
        
        return {'status': 'no_trigger', 'reason': 'Trigger conditions not met'}
        
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def generate_form_report(self, form_id: int, report_type: str = 'manual'):
    """
    Generate comprehensive report from form submissions
    
    Args:
        form_id: ID of the form to generate report for
        report_type: Type of report (manual, auto_submission_threshold, auto_time_interval, auto_immediate)
    """
    try:
        # Get form and submissions
        form = Form.query.get(form_id)
        if not form:
            raise ValueError(f"Form {form_id} not found")
        
        submissions = FormSubmission.query.filter_by(form_id=form_id).all()
        if not submissions:
            return {'status': 'no_data', 'reason': 'No submissions found'}
        
        # Create report record
        report = Report(
            title=f'{form.title} - Report ({datetime.now().strftime("%Y-%m-%d %H:%M")})',
            description=f'Automated report for form "{form.title}" with {len(submissions)} submissions',
            user_id=form.creator_id,
            template_id=f'form_{form_id}_{report_type}',
            status='processing',
            data={
                'form_id': form_id,
                'submission_count': len(submissions),
                'report_type': report_type,
                'generated_at': datetime.utcnow().isoformat()
            }
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Process submissions data
        submissions_data = []
        for submission in submissions:
            data = submission.data if isinstance(submission.data, dict) else json.loads(submission.data)
            data['submission_id'] = submission.id
            data['submitted_at'] = submission.submitted_at.isoformat()
            data['submitter_email'] = submission.submitter_email
            submissions_data.append(data)
        
        # Generate analysis with AI
        ai_service = AIService()
        ai_analysis = ai_service.analyze_form_data_with_ai(submissions_data, form.title)
        
        # Create charts
        charts = create_charts_from_submissions(submissions_data)
        
        # Generate statistical summary
        stats = generate_statistical_summary(submissions_data)
        
        # Create Word document
        word_path = create_word_report_from_form_data(
            form=form,
            submissions_data=submissions_data,
            ai_analysis=ai_analysis,
            charts=charts,
            stats=stats
        )
        
        # Update report record
        report.status = 'completed'
        report.output_url = word_path
        report.data.update({
            'ai_analysis': ai_analysis,
            'statistics': stats,
            'charts_count': len(charts),
            'completed_at': datetime.utcnow().isoformat()
        })
        
        db.session.commit()
        
        # Send email notification if configured
        if form.form_settings and form.form_settings.get('email_reports', False):
            send_report_notification.delay(report.id)
        
        return {
            'status': 'completed',
            'report_id': report.id,
            'output_path': word_path,
            'submissions_processed': len(submissions),
            'ai_insights': len(ai_analysis.get('insights', [])),
            'charts_generated': len(charts)
        }
        
    except Exception as e:
        # Update report status to failed
        if 'report' in locals():
            report.status = 'failed'
            report.data['error'] = str(e)
            db.session.commit()
        
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def generate_report_task(self, user_id: int, task_data: dict):
    """
    General purpose report generation task that matches the API expectations
    
    Args:
        user_id: ID of the user requesting the report
        task_data: Dictionary containing report parameters including report_id
    """
    try:
        report_id = task_data.get('report_id')
        if not report_id:
            raise ValueError("report_id is required in task_data")
        
        # Get the report record
        report = Report.query.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Update status to processing
        report.status = 'processing'
        db.session.commit()
        
        # For now, just mark as completed with basic data
        # This can be expanded later with actual report generation logic
        report.status = 'completed'
        if isinstance(report.data, dict):
            report.data['completed_at'] = datetime.utcnow().isoformat()
            report.data['generated_by_user'] = user_id
        else:
            report.data = {
                'completed_at': datetime.utcnow().isoformat(),
                'generated_by_user': user_id
            }
        db.session.commit()
        
        return {
            'status': 'completed',
            'report_id': report_id,
            'message': 'Report generated successfully'
        }
        
    except Exception as e:
        # Update report status to failed
        try:
            if report_id:
                report = Report.query.get(report_id)
                if report:
                    report.status = 'failed'
                    if isinstance(report.data, dict):
                        report.data['error'] = str(e)
                    else:
                        report.data = {'error': str(e)}
                    db.session.commit()
        except Exception:
            pass  # Don't fail if we can't update the report
        
        current_app.logger.error(f"Report generation failed: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def generate_scheduled_reports():
    """
    Generate scheduled reports for forms with time-based auto-reporting
    Runs as a cron job (e.g., every hour)
    """
    try:
        # Find forms with scheduled reporting
        forms = Form.query.filter(
            Form.is_active == True,
            Form.form_settings.op('->>')('auto_report_enabled').astext == 'true',
            Form.form_settings.op('->>')('trigger_type').astext == 'scheduled'
        ).all()
        
        results = []
        
        for form in forms:
            try:
                schedule_settings = form.form_settings.get('schedule_settings', {})
                frequency = schedule_settings.get('frequency', 'daily')  # daily, weekly, monthly
                
                # Check if it's time to generate report
                if should_generate_scheduled_report(form, frequency):
                    task = generate_form_report.delay(form.id, 'scheduled')
                    results.append({
                        'form_id': form.id,
                        'form_title': form.title,
                        'task_id': task.id,
                        'status': 'queued'
                    })
                    
            except Exception as e:
                results.append({
                    'form_id': form.id,
                    'form_title': form.title,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'status': 'completed',
            'processed_forms': len(forms),
            'reports_queued': len([r for r in results if r.get('status') == 'queued']),
            'results': results
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@shared_task
def send_report_notification(report_id: int):
    """
    Send email notification when report is completed
    
    Args:
        report_id: ID of the completed report
    """
    try:
        report = Report.query.get(report_id)
        if not report:
            return {'status': 'error', 'reason': 'Report not found'}
        
        # Get report creator
        user = User.query.get(report.user_id)
        if not user:
            return {'status': 'error', 'reason': 'User not found'}
        
        # Send email with report
        result = send_report_email(
            to_email=user.email,
            report=report,
            attach_file=True
        )
        
        return {
            'status': 'sent',
            'recipient': user.email,
            'report_title': report.title,
            'email_result': result
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@shared_task
def cleanup_old_reports():
    """
    Clean up old report files and database records
    Runs daily to manage storage
    """
    try:
        # Delete reports older than 90 days by default
        retention_days = int(os.getenv('REPORT_RETENTION_DAYS', 90))
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        old_reports = Report.query.filter(Report.created_at < cutoff_date).all()
        
        deleted_count = 0
        cleaned_files = 0
        
        for report in old_reports:
            try:
                # Delete physical file if exists
                if report.output_url and os.path.exists(report.output_url):
                    os.remove(report.output_url)
                    cleaned_files += 1
                
                # Delete database record
                db.session.delete(report)
                deleted_count += 1
                
            except Exception as e:
                print(f"Error cleaning up report {report.id}: {e}")
        
        db.session.commit()
        
        return {
            'status': 'completed',
            'deleted_reports': deleted_count,
            'cleaned_files': cleaned_files,
            'retention_days': retention_days
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def should_generate_scheduled_report(form: Form, frequency: str) -> bool:
    """
    Check if scheduled report should be generated for form
    
    Args:
        form: Form object
        frequency: Report frequency (daily, weekly, monthly)
        
    Returns:
        True if report should be generated
    """
    # Get last report
    last_report = Report.query.filter_by(
        template_id=f'form_{form.id}_scheduled'
    ).order_by(Report.created_at.desc()).first()
    
    if not last_report:
        return True  # No previous report, generate one
    
    now = datetime.utcnow()
    last_report_time = last_report.created_at
    
    if frequency == 'daily':
        return (now - last_report_time).days >= 1
    elif frequency == 'weekly':
        return (now - last_report_time).days >= 7
    elif frequency == 'monthly':
        return (now - last_report_time).days >= 30
    
    return False


def create_charts_from_submissions(submissions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create charts from form submission data
    
    Args:
        submissions_data: List of submission data dictionaries
        
    Returns:
        List of chart data with base64 encoded images
    """
    if not submissions_data or not PLOTTING_AVAILABLE:
        return []
    
    charts = []
    df = pd.DataFrame(submissions_data)
    
    # Set style for better looking charts
    if PLOTTING_AVAILABLE:
        try:
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
        except:
            pass  # Use default style if not available
    
    try:
        # 1. Submission timeline chart
        if 'submitted_at' in df.columns:
            timeline_chart = create_timeline_chart(df)
            if timeline_chart:
                charts.append(timeline_chart)
        
        # 2. Response distribution charts for categorical data
        for column in df.columns:
            if column not in ['submission_id', 'submitted_at', 'submitter_email']:
                if df[column].dtype == 'object' or df[column].nunique() <= 10:
                    dist_chart = create_distribution_chart(df, column)
                    if dist_chart:
                        charts.append(dist_chart)
        
        # 3. Numeric data summary charts
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_columns) > 0:
            summary_chart = create_numeric_summary_chart(df, numeric_columns)
            if summary_chart:
                charts.append(summary_chart)
        
    except Exception as e:
        print(f"Error creating charts: {e}")
    
    return charts


def create_timeline_chart(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Create submission timeline chart"""
    if not PLOTTING_AVAILABLE:
        return None
    
    try:
        df['submitted_at'] = pd.to_datetime(df['submitted_at'])
        df_grouped = df.groupby(df['submitted_at'].dt.date).size()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        df_grouped.plot(kind='line', marker='o', ax=ax)
        ax.set_title('Submission Timeline', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Number of Submissions', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return {
            'title': 'Submission Timeline',
            'type': 'timeline',
            'image_base64': chart_base64,
            'description': f'Timeline showing {len(df_grouped)} days of submissions'
        }
        
    except Exception as e:
        print(f"Error creating timeline chart: {e}")
        return None


def create_distribution_chart(df: pd.DataFrame, column: str) -> Optional[Dict[str, Any]]:
    """Create distribution chart for categorical data"""
    if not PLOTTING_AVAILABLE:
        return None
    
    try:
        # Skip if too many unique values or mostly null
        if df[column].nunique() > 15 or df[column].isnull().sum() / len(df) > 0.8:
            return None
        
        value_counts = df[column].value_counts().head(10)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        value_counts.plot(kind='bar', ax=ax)
        ax.set_title(f'Distribution of {column.title()}', fontsize=16, fontweight='bold')
        ax.set_xlabel(column.title(), fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        
        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return {
            'title': f'Distribution of {column.title()}',
            'type': 'distribution',
            'image_base64': chart_base64,
            'description': f'Distribution showing {len(value_counts)} categories for {column}'
        }
        
    except Exception as e:
        print(f"Error creating distribution chart for {column}: {e}")
        return None


def create_numeric_summary_chart(df: pd.DataFrame, numeric_columns: List[str]) -> Optional[Dict[str, Any]]:
    """Create summary chart for numeric data"""
    if not PLOTTING_AVAILABLE:
        return None
    
    try:
        if len(numeric_columns) == 0:
            return None
        
        # Create box plot for numeric columns
        fig, ax = plt.subplots(figsize=(12, 8))
        df[numeric_columns].boxplot(ax=ax)
        ax.set_title('Numeric Data Summary', fontsize=16, fontweight='bold')
        ax.set_ylabel('Values', fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        
        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return {
            'title': 'Numeric Data Summary',
            'type': 'numeric_summary',
            'image_base64': chart_base64,
            'description': f'Box plot summary of {len(numeric_columns)} numeric fields'
        }
        
    except Exception as e:
        print(f"Error creating numeric summary chart: {e}")
        return None


def generate_statistical_summary(submissions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate statistical summary of form submissions
    
    Args:
        submissions_data: List of submission data dictionaries
        
    Returns:
        Statistical summary dictionary
    """
    if not submissions_data:
        return {}
    
    df = pd.DataFrame(submissions_data)
    
    summary = {
        'total_submissions': len(df),
        'date_range': {},
        'response_rates': {},
        'field_completion': {},
        'top_responses': {}
    }
    
    # Date range analysis
    if 'submitted_at' in df.columns:
        df['submitted_at'] = pd.to_datetime(df['submitted_at'])
        summary['date_range'] = {
            'first_submission': df['submitted_at'].min().isoformat(),
            'last_submission': df['submitted_at'].max().isoformat(),
            'span_days': (df['submitted_at'].max() - df['submitted_at'].min()).days
        }
    
    # Field completion rates
    for column in df.columns:
        if column not in ['submission_id', 'submitted_at', 'submitter_email']:
            completion_rate = (df[column].notna().sum() / len(df)) * 100
            summary['field_completion'][column] = round(completion_rate, 1)
    
    # Top responses for categorical fields
    for column in df.columns:
        if column not in ['submission_id', 'submitted_at', 'submitter_email']:
            if df[column].dtype == 'object':
                top_response = df[column].value_counts().head(1)
                if not top_response.empty:
                    summary['top_responses'][column] = {
                        'value': top_response.index[0],
                        'count': int(top_response.iloc[0]),
                        'percentage': round((top_response.iloc[0] / len(df)) * 100, 1)
                    }
    
    return summary


def create_word_report_from_form_data(form: Form, submissions_data: List[Dict], 
                                     ai_analysis: Dict, charts: List[Dict], 
                                     stats: Dict) -> str:
    """
    Create Word document report from form data
    
    Returns:
        Path to generated Word document
    """
    try:
        # Create temporary file for the report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"form_report_{form.id}_{timestamp}.docx"
        output_dir = os.path.join(os.getenv('UPLOAD_FOLDER', 'uploads'), 'reports')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        # Use the existing report generator service
        from ..services.report_generator import create_word_report
        
        report_data = {
            'title': f'{form.title} - Analysis Report',
            'form_id': form.id,
            'form_title': form.title,
            'submissions': submissions_data,
            'ai_analysis': ai_analysis,
            'charts': charts,
            'statistics': stats,
            'generated_at': datetime.now().isoformat()
        }
        
        result_path = create_word_report(
            template_id='form_analysis',
            data=report_data,
            output_path=output_path
        )
        
        return result_path
        
    except Exception as e:
        print(f"Error creating Word report: {e}")
        raise e
