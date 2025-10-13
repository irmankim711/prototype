"""
Cleanup Tasks for Automated Report Platform
Handles periodic cleanup of old reports and orphaned files
"""

from celery import shared_task
from celery.schedules import crontab
import logging
from datetime import datetime, timedelta

from .. import db
from ..services.report_lifecycle_service import report_lifecycle_service
from ..services.latex_conversion_service import latex_conversion_service

logger = logging.getLogger(__name__)

@shared_task
def scheduled_report_cleanup():
    """
    Scheduled task to clean up expired reports and orphaned files
    Runs daily at 2:00 AM
    """
    try:
        logger.info("Starting scheduled report cleanup task")
        
        # Perform cleanup
        result = report_lifecycle_service.cleanup_expired_reports()
        
        logger.info(f"Scheduled cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in scheduled cleanup task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

@shared_task
def cleanup_temp_files():
    """
    Clean up temporary files from LaTeX conversion
    Runs every 6 hours
    """
    try:
        logger.info("Starting temporary file cleanup task")
        
        # Clean up temp files
        latex_conversion_service.cleanup_temp_files(max_age_hours=6)
        
        logger.info("Temporary file cleanup completed")
        return {'status': 'completed', 'message': 'Temp files cleaned up'}
        
    except Exception as e:
        logger.error(f"Error in temp file cleanup task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

@shared_task
def storage_usage_report():
    """
    Generate storage usage report
    Runs weekly on Sunday at 1:00 AM
    """
    try:
        logger.info("Generating storage usage report")
        
        # Get storage usage
        usage = report_lifecycle_service.get_storage_usage()
        
        logger.info(f"Storage usage report generated: {usage}")
        return usage
        
    except Exception as e:
        logger.error(f"Error generating storage usage report: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

@shared_task
def force_cleanup():
    """
    Force immediate cleanup regardless of schedule
    Can be called manually or by admin
    """
    try:
        logger.info("Starting forced cleanup task")
        
        # Force cleanup
        result = report_lifecycle_service.force_cleanup()
        
        logger.info(f"Forced cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in forced cleanup task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

# Celery beat schedule configuration
# This should be configured in your Celery configuration
CELERY_BEAT_SCHEDULE = {
    'daily-report-cleanup': {
        'task': 'app.tasks.cleanup_tasks.scheduled_report_cleanup',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
    },
    'temp-file-cleanup': {
        'task': 'app.tasks.cleanup_tasks.cleanup_temp_files',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'weekly-storage-report': {
        'task': 'app.tasks.cleanup_tasks.storage_usage_report',
        'schedule': crontab(day_of_week=0, hour=1, minute=0),  # Sunday at 1:00 AM
    },
}
