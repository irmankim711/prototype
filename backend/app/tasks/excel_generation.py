"""
Celery tasks for Excel generation and data processing
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from celery import current_task

from .. import db, celery
from ..models import ExcelExport, FormDataSubmission, FormDataSource
from ..utils.excel_generator import ExcelGenerator
from ..utils.socket_events import emit_export_update

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='generate_excel_export')
def generate_excel_export(self, export_id: int, auto_trigger: bool = False):
    """
    Generate Excel file from form submissions
    """
    try:
        # Update task status
        self.update_state(state='PROCESSING', meta={'progress': 0, 'status': 'Starting export...'})
        
        # Get export configuration
        export = ExcelExport.query.get(export_id)
        if not export:
            raise ValueError(f"Export configuration {export_id} not found")
        
        # Update export status
        export.export_status = 'processing'
        export.started_at = datetime.utcnow()
        export.export_progress = 0
        db.session.commit()
        
        # Emit real-time update
        emit_export_update(export_id, {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting Excel export...',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Get data sources
        data_sources = FormDataSource.query.filter(
            FormDataSource.id.in_(export.data_sources)
        ).all()
        
        if not data_sources:
            raise ValueError("No valid data sources found for export")
        
        # Update progress
        self.update_state(state='PROCESSING', meta={'progress': 10, 'status': 'Collecting submission data...'})
        export.export_progress = 10
        db.session.commit()
        
        # Collect submissions
        submissions = collect_submissions_for_export(export, data_sources)
        
        export.total_submissions = len(submissions)
        db.session.commit()
        
        if not submissions:
            # No submissions to export
            export.export_status = 'completed'
            export.completed_at = datetime.utcnow()
            export.export_duration = int((export.completed_at - export.started_at).total_seconds())
            export.export_progress = 100
            db.session.commit()
            
            emit_export_update(export_id, {
                'status': 'completed',
                'progress': 100,
                'message': 'Export completed (no data to export)',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return {
                'status': 'completed',
                'message': 'Export completed successfully (no data to export)',
                'total_submissions': 0
            }
        
        # Update progress
        self.update_state(state='PROCESSING', meta={'progress': 30, 'status': 'Generating Excel file...'})
        export.export_progress = 30
        db.session.commit()
        
        # Generate Excel file
        excel_generator = ExcelGenerator(export, submissions)
        file_path, file_name, file_size = excel_generator.generate()
        
        # Update progress
        self.update_state(state='PROCESSING', meta={'progress': 80, 'status': 'Finalizing export...'})
        export.export_progress = 80
        db.session.commit()
        
        # Update export record with file information
        export.file_path = file_path
        export.file_name = file_name
        export.file_size = file_size
        export.processed_submissions = len(submissions)
        export.export_status = 'completed'
        export.completed_at = datetime.utcnow()
        export.export_duration = int((export.completed_at - export.started_at).total_seconds())
        export.export_progress = 100
        
        # Update included_in_exports for all submissions
        submission_ids = [s.id for s in submissions]
        FormDataSubmission.query.filter(
            FormDataSubmission.id.in_(submission_ids)
        ).update({
            FormDataSubmission.included_in_exports: db.func.coalesce(
                FormDataSubmission.included_in_exports, 
                []
            ) + [export_id]
        }, synchronize_session=False)
        
        db.session.commit()
        
        # Emit completion update
        emit_export_update(export_id, {
            'status': 'completed',
            'progress': 100,
            'message': 'Excel export completed successfully',
            'file_name': file_name,
            'file_size': file_size,
            'total_submissions': len(submissions),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Excel export {export_id} completed successfully")
        
        return {
            'status': 'completed',
            'message': 'Excel export completed successfully',
            'file_path': file_path,
            'file_name': file_name,
            'file_size': file_size,
            'total_submissions': len(submissions),
            'duration': export.export_duration
        }
        
    except Exception as e:
        logger.error(f"Excel export {export_id} failed: {str(e)}")
        
        # Update export status to error
        if 'export' in locals():
            export.export_status = 'error'
            export.completed_at = datetime.utcnow()
            if export.started_at:
                export.export_duration = int((export.completed_at - export.started_at).total_seconds())
            export.error_count = 1
            db.session.commit()
        
        # Emit error update
        emit_export_update(export_id, {
            'status': 'error',
            'message': f'Excel export failed: {str(e)}',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Re-raise the exception to mark task as failed
        raise e

@celery.task(name='cleanup_old_exports')
def cleanup_old_exports(days_to_keep: int = 30):
    """
    Clean up old Excel export files and database records
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Find old exports
        old_exports = ExcelExport.query.filter(
            ExcelExport.created_at < cutoff_date,
            ExcelExport.export_status.in_(['completed', 'error'])
        ).all()
        
        deleted_count = 0
        error_count = 0
        
        for export in old_exports:
            try:
                # Delete file if it exists
                if export.file_path and os.path.exists(export.file_path):
                    os.remove(export.file_path)
                
                # Delete database record
                db.session.delete(export)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting export {export.id}: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        logger.info(f"Cleanup completed: {deleted_count} exports deleted, {error_count} errors")
        
        return {
            'status': 'completed',
            'deleted_count': deleted_count,
            'error_count': error_count
        }
        
    except Exception as e:
        logger.error(f"Export cleanup failed: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

@celery.task(name='auto_sync_data_sources')
def auto_sync_data_sources():
    """
    Automatically sync data sources that have auto_sync enabled
    """
    try:
        from ..utils.form_processors import FormProcessor
        from ..models import FormSyncLog
        
        # Find data sources that need syncing
        now = datetime.utcnow()
        sync_threshold = timedelta(minutes=5)  # Default minimum sync interval
        
        data_sources = FormDataSource.query.filter(
            FormDataSource.is_active == True,
            FormDataSource.auto_sync == True,
            db.or_(
                FormDataSource.last_sync.is_(None),
                FormDataSource.last_sync < now - sync_threshold
            )
        ).all()
        
        sync_results = []
        
        for data_source in data_sources:
            try:
                # Check if enough time has passed since last sync
                if data_source.last_sync:
                    time_since_sync = now - data_source.last_sync
                    required_interval = timedelta(seconds=data_source.sync_interval)
                    
                    if time_since_sync < required_interval:
                        continue  # Skip this data source
                
                # Perform sync
                processor = FormProcessor(data_source)
                result = processor.manual_sync()
                
                # Log the sync activity
                sync_log = FormSyncLog(
                    data_source_id=data_source.id,
                    sync_type='scheduled',
                    sync_status=result['status'],
                    new_submissions=result.get('new_submissions', 0),
                    updated_submissions=result.get('updated_submissions', 0),
                    error_count=result.get('error_count', 0),
                    sync_details=result.get('details', {}),
                    error_details=result.get('errors', {})
                )
                db.session.add(sync_log)
                
                # Update last sync time
                data_source.last_sync = now
                
                sync_results.append({
                    'data_source_id': data_source.id,
                    'status': result['status'],
                    'new_submissions': result.get('new_submissions', 0)
                })
                
            except Exception as e:
                logger.error(f"Auto sync failed for data source {data_source.id}: {str(e)}")
                sync_results.append({
                    'data_source_id': data_source.id,
                    'status': 'error',
                    'error': str(e)
                })
        
        db.session.commit()
        
        logger.info(f"Auto sync completed for {len(sync_results)} data sources")
        
        return {
            'status': 'completed',
            'synced_count': len(sync_results),
            'results': sync_results
        }
        
    except Exception as e:
        logger.error(f"Auto sync task failed: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

@celery.task(name='process_pending_submissions')
def process_pending_submissions():
    """
    Process any submissions that are still in pending status
    """
    try:
        from ..utils.form_processors import FormProcessor
        
        # Find pending submissions
        pending_submissions = FormDataSubmission.query.filter_by(
            processing_status='pending'
        ).limit(100).all()  # Process in batches
        
        processed_count = 0
        error_count = 0
        
        for submission in pending_submissions:
            try:
                # Get the data source
                data_source = submission.data_source
                if not data_source:
                    continue
                
                # Re-process the submission
                processor = FormProcessor(data_source)
                normalized_data = processor._normalize_submission_data(
                    submission.raw_data, 
                    data_source.source_type
                )
                
                submission.normalized_data = normalized_data
                submission.processing_status = 'processed'
                submission.updated_at = datetime.utcnow()
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing submission {submission.id}: {str(e)}")
                submission.processing_status = 'error'
                submission.processing_notes = str(e)
                error_count += 1
        
        db.session.commit()
        
        logger.info(f"Processed {processed_count} pending submissions, {error_count} errors")
        
        return {
            'status': 'completed',
            'processed_count': processed_count,
            'error_count': error_count
        }
        
    except Exception as e:
        logger.error(f"Process pending submissions failed: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

def collect_submissions_for_export(export: ExcelExport, data_sources: List[FormDataSource]) -> List[FormDataSubmission]:
    """
    Collect form submissions based on export configuration
    """
    try:
        # Base query
        query = FormDataSubmission.query.filter(
            FormDataSubmission.data_source_id.in_([ds.id for ds in data_sources]),
            FormDataSubmission.processing_status == 'processed'
        )
        
        # Apply date range filters
        if export.date_range_start:
            query = query.filter(FormDataSubmission.submitted_at >= export.date_range_start)
        
        if export.date_range_end:
            query = query.filter(FormDataSubmission.submitted_at <= export.date_range_end)
        
        # Apply additional filters if configured
        filters = export.filters or {}
        
        if filters.get('submitter_email'):
            query = query.filter(FormDataSubmission.submitter_email.like(f"%{filters['submitter_email']}%"))
        
        if filters.get('exclude_duplicates'):
            # Exclude submissions that have already been included in exports
            query = query.filter(
                db.or_(
                    FormDataSubmission.included_in_exports.is_(None),
                    FormDataSubmission.included_in_exports == []
                )
            )
        
        # Order by submission date
        query = query.order_by(FormDataSubmission.submitted_at.desc())
        
        # Apply limit if specified
        if filters.get('max_submissions'):
            query = query.limit(int(filters['max_submissions']))
        
        return query.all()
        
    except Exception as e:
        logger.error(f"Error collecting submissions for export: {str(e)}")
        return []
