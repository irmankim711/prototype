"""
Enhanced Celery Tasks with Retry Logic and Progress Tracking
Production-ready background tasks for the AI reporting platform
"""

from celery import shared_task, current_task
from datetime import datetime, timedelta
import json
import os
import logging
import time
from typing import Dict, List, Any, Optional

from .celery_enhanced import with_retry, CircuitBreaker, TaskProgressTracker, TaskMetrics
from .models import db, Form, FormSubmission, Report, User
from .services.ai_service import AIService
from .services.report_generator import ReportGenerator
from .services.email_service import EmailService
from .services.google_sheets_service import GoogleSheetsService
from .services.word_service import WordService

# Initialize services
logger = logging.getLogger(__name__)
ai_service = AIService()
report_generator = ReportGenerator()
email_service = EmailService()
google_sheets_service = GoogleSheetsService()
word_service = WordService()

# Initialize tracking and metrics
from flask import current_app
import redis

def get_redis_client():
    """Get Redis client for progress tracking"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    return redis.from_url(redis_url)

def get_progress_tracker():
    """Get task progress tracker"""
    return TaskProgressTracker(get_redis_client())

def get_task_metrics():
    """Get task metrics collector"""
    return TaskMetrics(get_redis_client())


@shared_task(bind=True, max_retries=3)
@with_retry(max_retries=3, countdown=60, backoff=True)
def generate_ai_report_task(self, user_id: int, form_id: int, report_config: Dict[str, Any]):
    """
    Generate AI-powered report from form submissions
    Enhanced with retry logic and progress tracking
    """
    task_id = self.request.id
    progress_tracker = get_progress_tracker()
    metrics = get_task_metrics()
    
    try:
        # Record task start
        metrics.record_task_start(task_id, 'generate_ai_report', 'reports')
        progress_tracker.update_progress(task_id, 0, "Starting AI report generation...")
        
        # Validate inputs
        form = Form.query.get(form_id)
        user = User.query.get(user_id)
        
        if not form or not user:
            raise ValueError(f"Invalid form_id ({form_id}) or user_id ({user_id})")
        
        progress_tracker.update_progress(task_id, 10, "Loading form submissions...")
        
        # Get form submissions
        submissions = FormSubmission.query.filter_by(form_id=form_id).all()
        if not submissions:
            raise ValueError(f"No submissions found for form {form_id}")
        
        progress_tracker.update_progress(task_id, 20, "Analyzing submission data...")
        
        # Prepare data for AI analysis
        submission_data = []
        for submission in submissions:
            submission_data.append({
                'id': submission.id,
                'data': submission.data,
                'created_at': submission.created_at.isoformat(),
                'metadata': submission.metadata or {}
            })
        
        progress_tracker.update_progress(task_id, 40, "Generating AI insights...")
        
        # Generate AI insights with circuit breaker
        @CircuitBreaker(failure_threshold=3, recovery_timeout=300)
        def generate_insights():
            return ai_service.analyze_form_data(
                form_data=submission_data,
                form_schema=form.schema,
                analysis_type=report_config.get('analysis_type', 'comprehensive')
            )
        
        ai_insights = generate_insights()
        
        progress_tracker.update_progress(task_id, 60, "Creating report document...")
        
        # Generate report document
        report_data = {
            'form_title': form.title,
            'form_description': form.description,
            'total_submissions': len(submissions),
            'analysis_period': {
                'start': min(s.created_at for s in submissions).isoformat(),
                'end': max(s.created_at for s in submissions).isoformat()
            },
            'ai_insights': ai_insights,
            'metadata': {
                'generated_by': user.email,
                'generated_at': datetime.utcnow().isoformat(),
                'config': report_config
            }
        }
        
        progress_tracker.update_progress(task_id, 80, "Generating report files...")
        
        # Generate different report formats based on config
        report_files = {}
        
        if report_config.get('generate_pdf', True):
            pdf_path = report_generator.create_pdf_report(report_data)
            report_files['pdf'] = pdf_path
        
        if report_config.get('generate_docx', True):
            docx_path = report_generator.create_docx_report(report_data)
            report_files['docx'] = docx_path
        
        if report_config.get('generate_excel', False):
            excel_path = report_generator.create_excel_report(submission_data, report_data)
            report_files['excel'] = excel_path
        
        progress_tracker.update_progress(task_id, 90, "Saving report to database...")
        
        # Save report to database
        report = Report(
            user_id=user_id,
            form_id=form_id,
            title=f"AI Report: {form.title}",
            content=json.dumps(report_data),
            status='completed',
            file_paths=json.dumps(report_files),
            metadata={
                'task_id': task_id,
                'generation_time': time.time() - metrics.get_start_time(task_id),
                'ai_provider': ai_service.get_current_provider()
            }
        )
        
        db.session.add(report)
        db.session.commit()
        
        progress_tracker.update_progress(task_id, 100, "Report generation completed!")
        
        # Record successful completion
        metrics.record_task_completion(task_id, success=True)
        
        # Send notification email if requested
        if report_config.get('send_email', False):
            send_report_email_task.delay(user_id, report.id)
        
        return {
            'status': 'completed',
            'report_id': report.id,
            'file_paths': report_files,
            'insights_count': len(ai_insights.get('insights', [])),
            'processing_time': time.time() - metrics.get_start_time(task_id)
        }
        
    except Exception as exc:
        # Record failure and update progress
        metrics.record_task_completion(task_id, success=False, error=exc)
        progress_tracker.update_progress(task_id, -1, f"Error: {str(exc)}")
        
        logger.error(
            f"AI report generation failed for user {user_id}, form {form_id}: {exc}",
            extra={'task_id': task_id, 'user_id': user_id, 'form_id': form_id}
        )
        
        raise exc


@shared_task(bind=True, max_retries=5)
@with_retry(max_retries=5, countdown=30, backoff=True)
def export_to_google_sheets_task(self, user_id: int, form_id: int, export_config: Dict[str, Any]):
    """
    Export form submissions to Google Sheets
    Enhanced with OAuth2 integration and error handling
    """
    task_id = self.request.id
    progress_tracker = get_progress_tracker()
    
    try:
        progress_tracker.update_progress(task_id, 0, "Starting Google Sheets export...")
        
        # Validate inputs
        form = Form.query.get(form_id)
        user = User.query.get(user_id)
        
        if not form or not user:
            raise ValueError(f"Invalid form_id ({form_id}) or user_id ({user_id})")
        
        progress_tracker.update_progress(task_id, 20, "Authenticating with Google Sheets...")
        
        # Authenticate with Google Sheets API
        @CircuitBreaker(failure_threshold=3, recovery_timeout=180)
        def authenticate_google():
            return google_sheets_service.authenticate_user(user_id)
        
        credentials = authenticate_google()
        
        progress_tracker.update_progress(task_id, 40, "Preparing data for export...")
        
        # Get form submissions
        submissions = FormSubmission.query.filter_by(form_id=form_id).all()
        
        # Prepare spreadsheet data
        headers = []
        for field in form.schema.get('fields', []):
            headers.append(field.get('label', field.get('id', 'Unknown')))
        
        headers.extend(['Submission ID', 'Submitted At', 'IP Address'])
        
        rows = [headers]
        
        for submission in submissions:
            row = []
            for field in form.schema.get('fields', []):
                field_id = field.get('id')
                value = submission.data.get(field_id, '')
                row.append(str(value) if value is not None else '')
            
            row.extend([
                submission.id,
                submission.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                submission.metadata.get('ip_address', '') if submission.metadata else ''
            ])
            rows.append(row)
        
        progress_tracker.update_progress(task_id, 70, "Creating Google Sheets spreadsheet...")
        
        # Create or update spreadsheet
        spreadsheet_title = export_config.get('title', f"{form.title} - Submissions")
        
        if export_config.get('spreadsheet_id'):
            # Update existing spreadsheet
            spreadsheet_url = google_sheets_service.update_spreadsheet(
                credentials,
                export_config['spreadsheet_id'],
                rows,
                export_config.get('sheet_name', 'Form Submissions')
            )
        else:
            # Create new spreadsheet
            spreadsheet_url = google_sheets_service.create_spreadsheet(
                credentials,
                spreadsheet_title,
                rows
            )
        
        progress_tracker.update_progress(task_id, 90, "Saving export record...")
        
        # Save export record
        export_record = {
            'task_id': task_id,
            'spreadsheet_url': spreadsheet_url,
            'exported_count': len(submissions),
            'exported_at': datetime.utcnow().isoformat()
        }
        
        # Update form metadata with export info
        if not form.metadata:
            form.metadata = {}
        
        if 'exports' not in form.metadata:
            form.metadata['exports'] = []
        
        form.metadata['exports'].append(export_record)
        db.session.commit()
        
        progress_tracker.update_progress(task_id, 100, "Export completed successfully!")
        
        return {
            'status': 'completed',
            'spreadsheet_url': spreadsheet_url,
            'exported_count': len(submissions),
            'export_id': task_id
        }
        
    except Exception as exc:
        progress_tracker.update_progress(task_id, -1, f"Export failed: {str(exc)}")
        logger.error(f"Google Sheets export failed: {exc}", extra={'task_id': task_id})
        raise exc


@shared_task(bind=True, max_retries=3)
@with_retry(max_retries=3, countdown=120, backoff=True)
def generate_word_document_task(self, user_id: int, template_id: int, data: Dict[str, Any]):
    """
    Generate Microsoft Word document from template
    Enhanced with Word API integration
    """
    task_id = self.request.id
    progress_tracker = get_progress_tracker()
    
    try:
        progress_tracker.update_progress(task_id, 0, "Starting Word document generation...")
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Invalid user_id: {user_id}")
        
        progress_tracker.update_progress(task_id, 20, "Loading template...")
        
        # Load template (this would be from a templates table/storage)
        template_data = word_service.load_template(template_id)
        
        progress_tracker.update_progress(task_id, 40, "Processing template with data...")
        
        # Process template with provided data
        @CircuitBreaker(failure_threshold=2, recovery_timeout=300)
        def process_template():
            return word_service.process_template(template_data, data)
        
        processed_content = process_template()
        
        progress_tracker.update_progress(task_id, 70, "Generating Word document...")
        
        # Generate Word document
        document_path = word_service.create_document(
            processed_content,
            filename=f"document_{task_id}_{int(time.time())}.docx"
        )
        
        progress_tracker.update_progress(task_id, 90, "Saving document record...")
        
        # Save document record to database
        document_record = {
            'task_id': task_id,
            'file_path': document_path,
            'template_id': template_id,
            'generated_by': user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'metadata': data.get('metadata', {})
        }
        
        progress_tracker.update_progress(task_id, 100, "Document generation completed!")
        
        return {
            'status': 'completed',
            'document_path': document_path,
            'document_id': task_id,
            'file_size': os.path.getsize(document_path) if os.path.exists(document_path) else 0
        }
        
    except Exception as exc:
        progress_tracker.update_progress(task_id, -1, f"Document generation failed: {str(exc)}")
        logger.error(f"Word document generation failed: {exc}", extra={'task_id': task_id})
        raise exc


@shared_task(bind=True, max_retries=2)
def send_report_email_task(self, user_id: int, report_id: int):
    """
    Send report via email with attachments
    """
    task_id = self.request.id
    
    try:
        user = User.query.get(user_id)
        report = Report.query.get(report_id)
        
        if not user or not report:
            raise ValueError(f"Invalid user_id ({user_id}) or report_id ({report_id})")
        
        # Prepare email content
        email_data = {
            'to': user.email,
            'subject': f"Your Report: {report.title}",
            'template': 'report_email.html',
            'context': {
                'user_name': user.first_name or user.email,
                'report_title': report.title,
                'generated_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'download_url': f"/api/reports/{report.id}/download"
            }
        }
        
        # Add attachments if available
        if report.file_paths:
            file_paths = json.loads(report.file_paths)
            email_data['attachments'] = []
            
            for format_type, file_path in file_paths.items():
                if os.path.exists(file_path):
                    email_data['attachments'].append({
                        'filename': f"report.{format_type}",
                        'path': file_path
                    })
        
        # Send email
        result = email_service.send_email(email_data)
        
        return {
            'status': 'sent',
            'email': user.email,
            'message_id': result.get('message_id')
        }
        
    except Exception as exc:
        logger.error(f"Email sending failed: {exc}", extra={'task_id': task_id})
        raise exc


# Maintenance and monitoring tasks

@shared_task
def cleanup_old_results():
    """Clean up old task results and temporary files"""
    try:
        redis_client = get_redis_client()
        current_time = time.time()
        
        # Clean up old progress tracking data
        for key in redis_client.scan_iter(match="task_progress:*"):
            data = redis_client.get(key)
            if data:
                progress_data = json.loads(data)
                if current_time - progress_data.get('updated_at', 0) > 86400:  # 24 hours
                    redis_client.delete(key)
        
        # Clean up old metrics data
        for key in redis_client.scan_iter(match="task_metrics:*"):
            data = redis_client.get(key)
            if data:
                metrics_data = json.loads(data)
                if current_time - metrics_data.get('start_time', 0) > 604800:  # 7 days
                    redis_client.delete(key)
        
        # Clean up old temporary files
        temp_dir = os.path.join(os.getcwd(), 'temp')
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 86400:  # 24 hours
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
        
        return {'status': 'completed', 'cleaned_at': datetime.utcnow().isoformat()}
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}")
        return {'status': 'failed', 'error': str(exc)}


@shared_task
def health_check():
    """Comprehensive health check for all services"""
    try:
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'unknown',
            'redis': 'unknown',
            'ai_service': 'unknown',
            'external_apis': {}
        }
        
        # Check database
        try:
            db.session.execute('SELECT 1')
            health_status['database'] = 'healthy'
        except Exception:
            health_status['database'] = 'unhealthy'
        
        # Check Redis
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            health_status['redis'] = 'healthy'
        except Exception:
            health_status['redis'] = 'unhealthy'
        
        # Check AI service
        try:
            ai_service.health_check()
            health_status['ai_service'] = 'healthy'
        except Exception:
            health_status['ai_service'] = 'unhealthy'
        
        # Check external APIs
        for service_name, service in [
            ('google_sheets', google_sheets_service),
            ('word_service', word_service)
        ]:
            try:
                if hasattr(service, 'health_check'):
                    service.health_check()
                health_status['external_apis'][service_name] = 'healthy'
            except Exception:
                health_status['external_apis'][service_name] = 'unhealthy'
        
        return health_status
        
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        return {'status': 'failed', 'error': str(exc)}


@shared_task
def collect_queue_metrics():
    """Collect and store queue metrics for monitoring"""
    try:
        from celery import current_app
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'queues': {},
            'workers': {}
        }
        
        # Get queue lengths
        with current_app.connection() as conn:
            for queue_name in ['default', 'reports', 'ai', 'exports', 'emails', 'high_priority']:
                try:
                    queue_length = conn.default_channel.queue_declare(
                        queue=queue_name, passive=True
                    ).method.message_count
                    metrics['queues'][queue_name] = queue_length
                except Exception:
                    metrics['queues'][queue_name] = -1
        
        # Get worker statistics
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            for worker_name, worker_stats in stats.items():
                metrics['workers'][worker_name] = {
                    'processed': worker_stats.get('total', 0),
                    'active': len(inspect.active().get(worker_name, [])),
                    'load': worker_stats.get('rusage', {}).get('utime', 0)
                }
        
        # Store metrics in Redis for dashboard
        redis_client = get_redis_client()
        redis_client.setex(
            'celery_metrics:latest',
            300,  # 5 minutes
            json.dumps(metrics)
        )
        
        # Store historical metrics
        redis_client.lpush('celery_metrics:history', json.dumps(metrics))
        redis_client.ltrim('celery_metrics:history', 0, 288)  # Keep 24 hours (5-min intervals)
        
        return metrics
        
    except Exception as exc:
        logger.error(f"Metrics collection failed: {exc}")
        return {'status': 'failed', 'error': str(exc)}
