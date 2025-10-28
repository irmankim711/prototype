"""
Export File Cleanup Utility
Automatically cleans up old export files to prevent disk space exhaustion
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import threading

logger = logging.getLogger(__name__)


class ExportCleanupService:
    """
    Service for cleaning up old export files

    Features:
    - Automatic cleanup of files older than specified age
    - Disk space monitoring
    - Scheduled cleanup jobs
    - Manual cleanup triggers
    - Detailed logging and reporting
    """

    def __init__(self, export_folder: str, max_age_hours: int = 24, max_disk_usage_percent: float = 80.0):
        """
        Initialize the cleanup service

        Args:
            export_folder: Path to the exports directory
            max_age_hours: Maximum age of files before cleanup (default: 24 hours)
            max_disk_usage_percent: Maximum disk usage percentage before forced cleanup
        """
        self.export_folder = export_folder
        self.max_age_seconds = max_age_hours * 3600
        self.max_disk_usage_percent = max_disk_usage_percent
        self.cleanup_lock = threading.Lock()
        self.cleanup_stats = {
            'last_cleanup': None,
            'files_deleted': 0,
            'bytes_freed': 0,
            'errors': 0
        }

    def get_file_age_seconds(self, file_path: str) -> float:
        """Get age of file in seconds"""
        try:
            return time.time() - os.path.getmtime(file_path)
        except OSError:
            return 0

    def get_disk_usage_percent(self) -> float:
        """Get current disk usage percentage for the export folder"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.export_folder)
            return (used / total) * 100
        except Exception as e:
            logger.error(f"Error checking disk usage: {str(e)}")
            return 0.0

    def should_cleanup_file(self, file_path: str, force_cleanup: bool = False) -> bool:
        """
        Determine if a file should be cleaned up

        Args:
            file_path: Path to the file
            force_cleanup: Force cleanup regardless of age

        Returns:
            True if file should be deleted
        """
        # Skip directories
        if os.path.isdir(file_path):
            return False

        # Skip non-export files (basic safety check)
        filename = os.path.basename(file_path)
        if not (filename.endswith('.xlsx') or filename.endswith('.csv') or filename.endswith('.xls')):
            return False

        # Force cleanup
        if force_cleanup:
            return True

        # Check file age
        file_age = self.get_file_age_seconds(file_path)
        return file_age > self.max_age_seconds

    def cleanup_old_files(self, force: bool = False) -> Dict[str, Any]:
        """
        Clean up old export files

        Args:
            force: Force cleanup regardless of age (only if disk usage is high)

        Returns:
            Dictionary with cleanup statistics
        """
        with self.cleanup_lock:
            start_time = time.time()
            files_deleted = 0
            bytes_freed = 0
            errors = []

            try:
                # Ensure export folder exists
                if not os.path.exists(self.export_folder):
                    logger.warning(f"Export folder does not exist: {self.export_folder}")
                    return {
                        'success': False,
                        'error': 'Export folder not found',
                        'files_deleted': 0,
                        'bytes_freed': 0
                    }

                # Check disk usage
                disk_usage = self.get_disk_usage_percent()
                force_cleanup = force or (disk_usage > self.max_disk_usage_percent)

                if force_cleanup:
                    logger.warning(f"Disk usage at {disk_usage:.1f}% - forcing cleanup")

                # Scan export folder
                for filename in os.listdir(self.export_folder):
                    file_path = os.path.join(self.export_folder, filename)

                    try:
                        if self.should_cleanup_file(file_path, force_cleanup):
                            # Get file size before deletion
                            file_size = os.path.getsize(file_path)

                            # Delete file
                            os.remove(file_path)

                            files_deleted += 1
                            bytes_freed += file_size

                            logger.info(f"Deleted old export file: {filename} ({file_size} bytes)")

                    except Exception as e:
                        error_msg = f"Error deleting {filename}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)

                # Update stats
                self.cleanup_stats['last_cleanup'] = datetime.now().isoformat()
                self.cleanup_stats['files_deleted'] += files_deleted
                self.cleanup_stats['bytes_freed'] += bytes_freed
                self.cleanup_stats['errors'] += len(errors)

                elapsed_time = time.time() - start_time

                result = {
                    'success': True,
                    'files_deleted': files_deleted,
                    'bytes_freed': bytes_freed,
                    'bytes_freed_mb': round(bytes_freed / (1024 * 1024), 2),
                    'disk_usage_percent': disk_usage,
                    'force_cleanup': force_cleanup,
                    'elapsed_seconds': round(elapsed_time, 2),
                    'errors': errors if errors else None
                }

                logger.info(f"Cleanup completed: {files_deleted} files deleted, {result['bytes_freed_mb']} MB freed")

                return result

            except Exception as e:
                logger.error(f"Cleanup job failed: {str(e)}", exc_info=True)
                return {
                    'success': False,
                    'error': str(e),
                    'files_deleted': files_deleted,
                    'bytes_freed': bytes_freed
                }

    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics"""
        return {
            **self.cleanup_stats,
            'max_age_hours': self.max_age_seconds / 3600,
            'export_folder': self.export_folder,
            'disk_usage_percent': self.get_disk_usage_percent()
        }

    def list_old_files(self) -> List[Dict[str, Any]]:
        """
        List files that would be cleaned up

        Returns:
            List of file information dictionaries
        """
        old_files = []

        try:
            if not os.path.exists(self.export_folder):
                return old_files

            for filename in os.listdir(self.export_folder):
                file_path = os.path.join(self.export_folder, filename)

                if self.should_cleanup_file(file_path):
                    file_age_hours = self.get_file_age_seconds(file_path) / 3600
                    file_size = os.path.getsize(file_path)

                    old_files.append({
                        'filename': filename,
                        'path': file_path,
                        'age_hours': round(file_age_hours, 2),
                        'size_bytes': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })

            # Sort by age (oldest first)
            old_files.sort(key=lambda x: x['age_hours'], reverse=True)

        except Exception as e:
            logger.error(f"Error listing old files: {str(e)}")

        return old_files


# Global cleanup service instance
_cleanup_service = None


def get_cleanup_service(export_folder: str = None, max_age_hours: int = 24) -> ExportCleanupService:
    """Get or create the global cleanup service instance"""
    global _cleanup_service

    if _cleanup_service is None:
        if export_folder is None:
            export_folder = os.path.join(os.getcwd(), 'static', 'exports')
        _cleanup_service = ExportCleanupService(export_folder, max_age_hours)

    return _cleanup_service


def schedule_periodic_cleanup(interval_hours: int = 6):
    """
    Schedule periodic cleanup jobs

    Args:
        interval_hours: Hours between cleanup runs
    """
    import schedule
    import threading

    def run_cleanup():
        service = get_cleanup_service()
        logger.info("Running scheduled cleanup job")
        result = service.cleanup_old_files()
        logger.info(f"Scheduled cleanup result: {result}")

    # Schedule the job
    schedule.every(interval_hours).hours.do(run_cleanup)

    # Run scheduler in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    logger.info(f"Scheduled cleanup job to run every {interval_hours} hours")
