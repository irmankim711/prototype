"""
Report Lifecycle Management Service
Handles automatic cleanup of old reports and orphaned files
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import shutil

from .. import db
from ..models import Report, User
from ..services.latex_conversion_service import latex_conversion_service

logger = logging.getLogger(__name__)

class ReportLifecycleService:
    """Service for managing report lifecycle and cleanup"""
    
    def __init__(self, retention_days: int = 30, cleanup_interval_hours: int = 24):
        self.retention_days = retention_days
        self.cleanup_interval_hours = cleanup_interval_hours
        self.last_cleanup = None
        self.static_dir = os.path.join(os.getcwd(), 'static', 'generated')
        self.temp_dir = os.path.join(os.getcwd(), 'temp', 'latex_conversion')
    
    def cleanup_expired_reports(self, force: bool = False) -> Dict[str, Any]:
        """
        Clean up expired reports and their associated files
        
        Args:
            force: Force cleanup even if not due
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            # Check if cleanup is due
            if not force and self.last_cleanup:
                time_since_last = datetime.now() - self.last_cleanup
                if time_since_last.total_seconds() < (self.cleanup_interval_hours * 3600):
                    return {
                        'status': 'skipped',
                        'message': f'Cleanup not due yet. Next cleanup in {self.cleanup_interval_hours - (time_since_last.total_seconds() / 3600):.1f} hours',
                        'last_cleanup': self.last_cleanup.isoformat()
                    }
            
            logger.info(f"Starting report cleanup (retention: {self.retention_days} days)")
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Find expired reports
            expired_reports = Report.query.filter(
                Report.created_at < cutoff_date,
                Report.generation_status.in_(['completed', 'failed'])
            ).all()
            
            cleanup_results = {
                'status': 'completed',
                'reports_processed': len(expired_reports),
                'files_removed': 0,
                'storage_freed': 0,
                'errors': [],
                'removed_reports': []
            }
            
            for report in expired_reports:
                try:
                    # Remove report files
                    files_removed, storage_freed = self._remove_report_files(report)
                    cleanup_results['files_removed'] += files_removed
                    cleanup_results['storage_freed'] += storage_freed
                    
                    # Remove from database
                    db.session.delete(report)
                    cleanup_results['removed_reports'].append({
                        'id': report.id,
                        'title': report.title,
                        'created_at': report.created_at.isoformat()
                    })
                    
                    logger.info(f"Removed expired report: {report.id} - {report.title}")
                    
                except Exception as e:
                    error_msg = f"Error removing report {report.id}: {str(e)}"
                    cleanup_results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Commit database changes
            db.session.commit()
            
            # Clean up orphaned files
            orphaned_cleanup = self._cleanup_orphaned_files()
            cleanup_results['orphaned_files_removed'] = orphaned_cleanup['files_removed']
            cleanup_results['orphaned_storage_freed'] = orphaned_cleanup['storage_freed']
            
            # Clean up temporary files
            latex_conversion_service.cleanup_temp_files()
            
            # Update last cleanup time
            self.last_cleanup = datetime.now()
            
            logger.info(f"Report cleanup completed: {cleanup_results['reports_processed']} reports processed")
            
            return cleanup_results
            
        except Exception as e:
            error_msg = f"Error during report cleanup: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _remove_report_files(self, report: Report) -> tuple[int, int]:
        """Remove files associated with a report"""
        files_removed = 0
        storage_freed = 0
        
        # Only one file_path field in the actual database schema
        if report.file_path and os.path.exists(report.file_path):
            try:
                # Get file size before removal
                file_size = os.path.getsize(report.file_path)
                
                # Remove file
                os.remove(report.file_path)
                
                files_removed += 1
                storage_freed += file_size
                
                logger.debug(f"Removed file: {report.file_path}")
                
            except Exception as e:
                logger.warning(f"Failed to remove file {report.file_path}: {str(e)}")
        
        return files_removed, storage_freed
    
    def _cleanup_orphaned_files(self) -> Dict[str, int]:
        """Clean up orphaned files that don't have corresponding database records"""
        try:
            files_removed = 0
            storage_freed = 0
            
            # Get all files in static directory
            if not os.path.exists(self.static_dir):
                return {'files_removed': 0, 'storage_freed': 0}
            
            for filename in os.listdir(self.static_dir):
                file_path = os.path.join(self.static_dir, filename)
                
                if os.path.isfile(file_path):
                    # Check if file is referenced in database
                    if not self._is_file_referenced(filename):
                        try:
                            # Get file size before removal
                            file_size = os.path.getsize(file_path)
                            
                            # Remove orphaned file
                            os.remove(file_path)
                            
                            files_removed += 1
                            storage_freed += file_size
                            
                            logger.info(f"Removed orphaned file: {filename}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to remove orphaned file {filename}: {str(e)}")
            
            return {
                'files_removed': files_removed,
                'storage_freed': storage_freed
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned files: {str(e)}")
            return {'files_removed': 0, 'storage_freed': 0}
    
    def _is_file_referenced(self, filename: str) -> bool:
        """Check if a file is referenced in the database"""
        try:
            # Check if filename appears in any report file paths
            referenced = Report.query.filter(
                Report.file_path.like(f'%{filename}')
            ).first()
            
            return referenced is not None
            
        except Exception as e:
            logger.error(f"Error checking file reference: {str(e)}")
            return False  # Assume referenced to be safe
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get current storage usage statistics"""
        try:
            total_reports = Report.query.count()
            completed_reports = Report.query.filter(Report.generation_status == 'completed').count()
            failed_reports = Report.query.filter(Report.generation_status == 'failed').count()
            pending_reports = Report.query.filter(Report.generation_status == 'pending').count()
            
            # Calculate total storage used
            total_storage = 0
            report_count = 0
            
            for report in Report.query.filter(Report.generation_status == 'completed').all():
                # Use file_size field since specific format file sizes don't exist in database
                if report.file_size:
                    total_storage += report.file_size
                report_count += 1
            
            # Get directory sizes
            static_dir_size = self._get_directory_size(self.static_dir)
            temp_dir_size = self._get_directory_size(self.temp_dir)
            
            return {
                'total_reports': total_reports,
                'completed_reports': completed_reports,
                'failed_reports': failed_reports,
                'pending_reports': pending_reports,
                'total_storage_bytes': total_storage,
                'total_storage_mb': round(total_storage / (1024 * 1024), 2),
                'average_storage_per_report': round(total_storage / report_count, 2) if report_count > 0 else 0,
                'static_directory_size_mb': round(static_dir_size / (1024 * 1024), 2),
                'temp_directory_size_mb': round(temp_dir_size / (1024 * 1024), 2),
                'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
                'retention_days': self.retention_days,
                'next_cleanup_due': self._get_next_cleanup_time()
            }
            
        except Exception as e:
            logger.error(f"Error getting storage usage: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
    
    def _get_directory_size(self, directory_path: str) -> int:
        """Calculate total size of a directory"""
        try:
            if not os.path.exists(directory_path):
                return 0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            return total_size
            
        except Exception as e:
            logger.error(f"Error calculating directory size for {directory_path}: {str(e)}")
            return 0
    
    def _get_next_cleanup_time(self) -> Optional[str]:
        """Get the next scheduled cleanup time"""
        if not self.last_cleanup:
            return datetime.now().isoformat()
        
        next_cleanup = self.last_cleanup + timedelta(hours=self.cleanup_interval_hours)
        return next_cleanup.isoformat()
    
    def update_retention_policy(self, retention_days: int):
        """Update the retention policy"""
        self.retention_days = retention_days
        logger.info(f"Updated retention policy to {retention_days} days")
    
    def force_cleanup(self):
        """Force immediate cleanup regardless of schedule"""
        return self.cleanup_expired_reports(force=True)

# Global instance
report_lifecycle_service = ReportLifecycleService()
