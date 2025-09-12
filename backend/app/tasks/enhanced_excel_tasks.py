"""
Enhanced Excel Generation Tasks
Uses the EnhancedExcelService for robust Excel generation with progress tracking
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from celery import current_task
import traceback

from .. import db, celery
from ..models import ExcelExport, FormDataSubmission, FormDataSource
from ..services.enhanced_excel_service import EnhancedExcelService, ExcelValidationError, DataProcessingError
from ..utils.socket_events import emit_export_update

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='enhanced_excel_export')
def enhanced_excel_export(self, export_id: int, auto_trigger: bool = False) -> Dict[str, Any]:
    """
    Enhanced Excel export using the robust Excel service
    
    Args:
        export_id: ID of the export configuration
        auto_trigger: Whether this was triggered automatically
        
    Returns:
        Dictionary with export results and metadata
    """
    start_time = datetime.utcnow()
    
    try:
        # Update task status
        self.update_state(
            state='PROCESSING', 
            meta={
                'progress': 0, 
                'status': 'Starting enhanced Excel export...',
                'timestamp': start_time.isoformat()
            }
        )
        
        # Get export configuration
        export = ExcelExport.query.get(export_id)
        if not export:
            raise ValueError(f"Export configuration {export_id} not found")
        
        # Update export status
        export.export_status = 'processing'
        export.started_at = start_time
        export.export_progress = 0
        db.session.commit()
        
        # Emit real-time update
        emit_export_update(export_id, {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting enhanced Excel export...',
            'timestamp': start_time.isoformat()
        })
        
        # Update progress
        self._update_progress(5, "Validating export configuration...")
        
        # Get data sources
        data_sources = FormDataSource.query.filter(
            FormDataSource.id.in_(export.data_sources)
        ).all()
        
        if not data_sources:
            raise ValueError("No valid data sources found for export")
        
        # Update progress
        self._update_progress(10, "Collecting submission data...")
        
        # Collect submissions with progress updates
        submissions = collect_submissions_for_export_with_progress(
            export, 
            data_sources, 
            progress_callback=lambda p, msg: self._update_progress(10 + p * 0.2, msg)
        )
        
        export.total_submissions = len(submissions)
        db.session.commit()
        
        if not submissions:
            # No submissions to export
            return self._handle_empty_export(export, start_time)
        
        # Update progress
        self._update_progress(30, "Initializing enhanced Excel service...")
        
        # Configure enhanced Excel service
        excel_config = {
            'max_chunk_size': 1000,  # Process 1000 records at a time
            'max_memory_mb': 512,    # Limit memory usage to 512MB
            'validation_enabled': True,
            'progress_callback': lambda p, msg: self._update_progress(30 + p * 0.5, msg)
        }
        
        # Create enhanced Excel service
        excel_service = EnhancedExcelService(config=excel_config)
        
        try:
            # Update progress
            self._update_progress(35, "Generating Excel file with enhanced service...")
            
            # Generate Excel file
            excel_result = excel_service.generate_excel(
                data=submissions,
                output_path=self._get_output_path(export),
                template_config=export.template_config or {}
            )
            
            if not excel_result['success']:
                raise DataProcessingError(f"Excel generation failed: {excel_result['errors']}")
            
            # Update progress
            self._update_progress(85, "Finalizing export...")
            
            # Update export record with file information
            export.file_path = excel_result['file_path']
            export.file_name = os.path.basename(excel_result['file_path'])
            export.file_size = excel_result['file_size']
            export.processed_submissions = excel_result['processed_rows']
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
            
            # Update progress
            self._update_progress(100, "Excel export completed successfully!")
            
            # Emit completion update
            emit_export_update(export_id, {
                'status': 'completed',
                'progress': 100,
                'message': 'Enhanced Excel export completed successfully',
                'file_name': export.file_name,
                'file_size': export.file_size,
                'total_submissions': len(submissions),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Enhanced Excel export {export_id} completed successfully")
            
            # Clean up service
            excel_service.cleanup()
            
            return {
                'status': 'completed',
                'message': 'Enhanced Excel export completed successfully',
                'file_path': excel_result['file_path'],
                'file_name': export.file_name,
                'file_size': excel_result['file_size'],
                'total_submissions': len(submissions),
                'duration': export.export_duration,
                'memory_usage_mb': excel_result.get('memory_usage_mb', 0),
                'validation_passed': True
            }
            
        finally:
            # Always clean up
            excel_service.cleanup()
            
    except Exception as e:
        logger.error(f"Enhanced Excel export {export_id} failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update export status to error
        if 'export' in locals():
            export.export_status = 'error'
            export.completed_at = datetime.utcnow()
            if export.started_at:
                export.export_duration = int((export.completed_at - export.started_at).total_seconds())
            export.error_count = 1
            export.error_details = str(e)
            db.session.commit()
        
        # Emit error update
        emit_export_update(export_id, {
            'status': 'error',
            'message': f'Enhanced Excel export failed: {str(e)}',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Re-raise the exception to mark task as failed
        raise e

def collect_submissions_for_export_with_progress(
    export: ExcelExport, 
    data_sources: List[FormDataSource],
    progress_callback=None
) -> List[FormDataSubmission]:
    """
    Collect form submissions with progress updates
    
    Args:
        export: Export configuration
        data_sources: List of data sources
        progress_callback: Optional progress callback function
        
    Returns:
        List of form submissions
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
        
        # Get total count for progress tracking
        total_count = query.count()
        
        if progress_callback:
            progress_callback(0, f"Found {total_count} submissions to process")
        
        # Order by submission date
        query = query.order_by(FormDataSubmission.submitted_at.desc())
        
        # Apply limit if specified
        if filters.get('max_submissions'):
            query = query.limit(int(filters['max_submissions']))
            total_count = min(total_count, int(filters['max_submissions']))
        
        # Fetch all submissions
        submissions = query.all()
        
        if progress_callback:
            progress_callback(100, f"Successfully collected {len(submissions)} submissions")
        
        return submissions
        
    except Exception as e:
        logger.error(f"Error collecting submissions for export: {str(e)}")
        if progress_callback:
            progress_callback(0, f"Error collecting submissions: {str(e)}")
        return []

def _handle_empty_export(export: ExcelExport, start_time: datetime) -> Dict[str, Any]:
    """Handle case where there are no submissions to export"""
    export.export_status = 'completed'
    export.completed_at = datetime.utcnow()
    export.export_duration = int((export.completed_at - start_time).total_seconds())
    export.export_progress = 100
    db.session.commit()
    
    emit_export_update(export.id, {
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

def _get_output_path(export: ExcelExport) -> str:
    """Generate output path for Excel file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{export.name}_{timestamp}.xlsx"
    
    # Use reports directory from export config or default
    reports_dir = getattr(export, 'reports_directory', None) or 'reports'
    os.makedirs(reports_dir, exist_ok=True)
    
    return os.path.join(reports_dir, filename)

def _update_progress(percentage: float, message: str) -> None:
    """Update progress for the current task"""
    try:
        current_task.update_state(
            state='PROCESSING',
            meta={
                'progress': percentage,
                'status': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to update progress: {str(e)}")

@celery.task(name='validate_excel_file')
def validate_excel_file(file_path: str) -> Dict[str, Any]:
    """
    Validate an existing Excel file
    
    Args:
        file_path: Path to the Excel file to validate
        
    Returns:
        Validation results
    """
    try:
        if not os.path.exists(file_path):
            return {
                'valid': False,
                'errors': ['File does not exist'],
                'file_path': file_path
            }
        
        # Create enhanced Excel service for validation
        excel_service = EnhancedExcelService(config={'validation_enabled': True})
        
        try:
            # Validate the file
            validation_result = excel_service._validate_excel_output(file_path, [])
            
            return {
                'valid': validation_result['valid'],
                'errors': validation_result['errors'],
                'warnings': validation_result['warnings'],
                'file_size_mb': validation_result['file_size_mb'],
                'row_count': validation_result['row_count'],
                'column_count': validation_result['column_count'],
                'file_path': file_path
            }
            
        finally:
            excel_service.cleanup()
            
    except Exception as e:
        logger.error(f"Excel validation failed: {str(e)}")
        return {
            'valid': False,
            'errors': [f'Validation failed: {str(e)}'],
            'file_path': file_path
        }

@celery.task(name='cleanup_excel_files')
def cleanup_excel_files(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old Excel export files
    
    Args:
        days_to_keep: Number of days to keep files
        
    Returns:
        Cleanup results
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
        
        logger.info(f"Excel cleanup completed: {deleted_count} exports deleted, {error_count} errors")
        
        return {
            'status': 'completed',
            'deleted_count': deleted_count,
            'error_count': error_count
        }
        
    except Exception as e:
        logger.error(f"Excel cleanup failed: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
