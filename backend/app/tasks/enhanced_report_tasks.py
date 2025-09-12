"""
Enhanced Celery Tasks for Automated Report Generation
Handles background processing of form data and comprehensive report creation
"""

from celery import shared_task
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
from flask import current_app

from .. import db
from ..models import Form, FormSubmission, Report, User
from ..services.report_generation_service import report_generation_service
from ..services.excel_export_service import excel_export_service
from ..core.exceptions import ReportGenerationError

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_comprehensive_report_task(self, report_id: int, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive report with all formats (PDF, DOCX, Excel)
    
    Args:
        report_id: ID of the report record
        data: Data to include in the report
        config: Report configuration
        
    Returns:
        Dictionary with generation results
    """
    try:
        logger.info(f"Starting comprehensive report generation for report {report_id}")
        
        # Generate the comprehensive report
        result = report_generation_service.generate_comprehensive_report(report_id, data, config)
        
        logger.info(f"Comprehensive report {report_id} generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report {report_id}: {str(e)}")
        
        # Update report status to failed
        try:
            report = Report.query.get(report_id)
            if report:
                report.update_status('failed', error_message=str(e))
                db.session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update report status: {str(db_error)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying report generation {report_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for report {report_id}")
            raise ReportGenerationError(f"Failed to generate report after {self.max_retries} attempts: {str(e)}")

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def export_form_to_excel_task(self, form_id: int, user_id: int, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Export form submissions to Excel in the background
    
    Args:
        form_id: ID of the form to export
        user_id: ID of the user requesting export
        options: Export options
        
    Returns:
        Dictionary with export results
    """
    try:
        logger.info(f"Starting Excel export for form {form_id}")
        
        # Export form submissions to Excel
        file_path, file_size = excel_export_service.export_form_submissions(form_id, user_id, options)
        
        # Generate download URL
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        download_url = f"{base_url}/api/forms/{form_id}/download-excel"
        
        result = {
            'status': 'completed',
            'form_id': form_id,
            'file_path': file_path,
            'file_size': file_size,
            'download_url': download_url,
            'exported_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Excel export completed for form {form_id}: {file_path}")
        return result
        
    except Exception as e:
        logger.error(f"Error exporting form {form_id} to Excel: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying Excel export for form {form_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for Excel export of form {form_id}")
            raise ExportError(f"Failed to export form to Excel after {self.max_retries} attempts: {str(e)}")

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_generate_form_report_task(self, form_id: int, submission_id: int = None) -> Dict[str, Any]:
    """
    Automatically generate a report when new form submission is received
    
    Args:
        form_id: ID of the form that received submission
        submission_id: ID of the new submission (optional)
        
    Returns:
        Dictionary with generation results
    """
    try:
        logger.info(f"Starting auto-report generation for form {form_id}")
        
        # Get form and check auto-reporting settings
        form = Form.query.get(form_id)
        if not form:
            raise ReportGenerationError(f"Form {form_id} not found")
        
        # Check if auto-reporting is enabled
        form_settings = form.form_settings or {}
        if not form_settings.get('auto_report_enabled', False):
            logger.info(f"Auto-reporting not enabled for form {form_id}")
            return {'status': 'skipped', 'reason': 'Auto-reporting not enabled'}
        
        # Get auto-report settings
        report_settings = form_settings.get('auto_report_settings', {})
        trigger_type = report_settings.get('trigger_type', 'submission_count')
        
        should_generate = False
        trigger_reason = ''
        
        if trigger_type == 'submission_count':
            threshold = report_settings.get('submission_threshold', 10)
            submission_count = FormSubmission.query.filter_by(form_id=form_id).count()
            
            if submission_count >= threshold and submission_count % threshold == 0:
                should_generate = True
                trigger_reason = f'submission_count_threshold_{threshold}'
        
        elif trigger_type == 'time_interval':
            interval_hours = report_settings.get('interval_hours', 24)
            
            # Check if enough time has passed since last report
            last_report = Report.query.filter_by(
                source_form_id=form_id,
                report_type='auto_generated'
            ).order_by(Report.created_at.desc()).first()
            
            if not last_report or (datetime.utcnow() - last_report.created_at).total_seconds() >= interval_hours * 3600:
                should_generate = True
                trigger_reason = f'time_interval_{interval_hours}h'
        
        elif trigger_type == 'immediate' and submission_id:
            # Generate report immediately for each submission
            should_generate = True
            trigger_reason = 'immediate_submission'
        
        if not should_generate:
            logger.info(f"Auto-report conditions not met for form {form_id}")
            return {'status': 'skipped', 'reason': 'Conditions not met'}
        
        # Create report record
        report = Report(
            title=f"Auto-Generated Report - {form.title}",
            description=f"Automatically generated report for form {form.title}",
            report_type='auto_generated',
            status='pending',
            user_id=form.creator_id,
            source_form_id=form_id,
            report_config={
                'auto_generated': True,
                'trigger_type': trigger_type,
                'trigger_reason': trigger_reason,
                'generation_config': report_settings
            }
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Get form data for report generation
        submissions = FormSubmission.query.filter_by(form_id=form_id).all()
        
        # Prepare report data
        report_data = {
            'form_info': {
                'id': form.id,
                'title': form.title,
                'description': form.description,
                'created_at': form.created_at.isoformat() if form.created_at else None
            },
            'submissions': [
                {
                    'id': sub.id,
                    'data': sub.data,
                    'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None,
                    'status': sub.status,
                    'submitter_email': sub.submitter_email
                }
                for sub in submissions
            ],
            'summary': {
                'total_submissions': len(submissions),
                'generation_trigger': trigger_reason,
                'generated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Generate report configuration
        report_config = {
            'title': f"Auto-Generated Report - {form.title}",
            'base_url': current_app.config.get('BASE_URL', 'http://localhost:5000'),
            'excel_config': {
                'sheet_name': f"Form_{form.id}_Submissions"
            }
        }
        
        # Start report generation
        generate_comprehensive_report_task.delay(report.id, report_data, report_config)
        
        logger.info(f"Auto-report generation initiated for form {form_id}, report {report.id}")
        
        return {
            'status': 'initiated',
            'report_id': report.id,
            'trigger_reason': trigger_reason,
            'form_id': form_id
        }
        
    except Exception as e:
        logger.error(f"Error in auto-report generation for form {form_id}: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying auto-report generation for form {form_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for auto-report generation of form {form_id}")
            raise ReportGenerationError(f"Failed to auto-generate report after {self.max_retries} attempts: {str(e)}")

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_old_reports_task(self) -> Dict[str, Any]:
    """
    Clean up old report files and database records
    
    Returns:
        Dictionary with cleanup results
    """
    try:
        logger.info("Starting cleanup of old reports")
        
        # Clean up old report files
        report_generation_service.cleanup_old_files(days_old=30)
        
        # Clean up old Excel exports
        excel_export_service.cleanup_old_exports(days_old=7)
        
        # Clean up old database records
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_reports = Report.query.filter(
            Report.created_at < cutoff_date,
            Report.status.in_(['completed', 'failed'])
        ).all()
        
        cleaned_count = 0
        for report in old_reports:
            try:
                # Remove file references
                report.pdf_file_path = None
                report.docx_file_path = None
                report.excel_file_path = None
                report.pdf_file_size = None
                report.docx_file_size = None
                report.excel_file_size = None
                report.status = 'archived'
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to clean up report {report.id}: {str(e)}")
        
        db.session.commit()
        
        result = {
            'status': 'completed',
            'cleaned_reports': cleaned_count,
            'cleanup_time': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Cleanup completed: {cleaned_count} reports cleaned")
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying cleanup task (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=300 * (2 ** self.request.retries))
        else:
            logger.error("Max retries exceeded for cleanup task")
            raise Exception(f"Failed to cleanup old reports after {self.max_retries} attempts: {str(e)}")

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def health_check_task(self) -> Dict[str, Any]:
    """
    Health check task for monitoring system status
    
    Returns:
        Dictionary with health status
    """
    try:
        logger.info("Starting health check")
        
        # Check database connectivity
        try:
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
        
        # Check Redis connectivity (if available)
        try:
            from .. import celery
            redis_status = 'healthy' if celery.control.inspect().active() else 'unhealthy'
        except Exception as e:
            redis_status = f'unhealthy: {str(e)}'
        
        # Check file system
        try:
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            import os
            if os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK):
                fs_status = 'healthy'
            else:
                fs_status = 'unhealthy: no write access'
        except Exception as e:
            fs_status = f'unhealthy: {str(e)}'
        
        result = {
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status,
            'redis': redis_status,
            'filesystem': fs_status,
            'overall_health': 'healthy' if all(s == 'healthy' for s in [db_status, redis_status, fs_status]) else 'degraded'
        }
        
        logger.info(f"Health check completed: {result['overall_health']}")
        return result
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying health check (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        else:
            logger.error("Max retries exceeded for health check")
            raise Exception(f"Failed to complete health check after {self.max_retries} attempts: {str(e)}")
