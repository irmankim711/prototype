"""
Cleanup Orphaned Files Utility

This utility helps identify and clean up orphaned files that exist in storage
but have no corresponding database records. This can happen if file deletion
fails but the database record was already deleted in older versions of the code.

Usage:
    python cleanup_orphaned_files.py [--dry-run] [--cleanup-postgresql] [--cleanup-firebase]
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Report
from app.services.firebase_storage_service import firebase_storage_service
from app.services.firestore_report_service import firestore_report_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_postgresql_orphaned_files(dry_run=True):
    """
    Find and clean up orphaned files from PostgreSQL-based reports

    Args:
        dry_run: If True, only report orphaned files without deleting them

    Returns:
        Tuple of (files_found, files_deleted)
    """
    logger.info("=" * 60)
    logger.info("Scanning PostgreSQL local storage for orphaned files...")
    logger.info("=" * 60)

    # Get all report file paths from database
    reports = Report.query.all()
    db_file_paths = set()

    for report in reports:
        if report.file_path:
            base_path = os.path.splitext(report.file_path)[0]
            for ext in ['pdf', 'docx', 'xlsx']:
                db_file_paths.add(f"{base_path}.{ext}")

    logger.info(f"Found {len(db_file_paths)} expected files in database")

    # Scan file system for actual files
    static_dir = os.path.join(os.path.dirname(__file__), 'static', 'reports')

    if not os.path.exists(static_dir):
        logger.warning(f"Reports directory does not exist: {static_dir}")
        return 0, 0

    orphaned_files = []

    for root, dirs, files in os.walk(static_dir):
        for file in files:
            file_path = os.path.join(root, file)

            # Check if this file is in the database
            if file_path not in db_file_paths:
                orphaned_files.append(file_path)

    logger.info(f"Found {len(orphaned_files)} orphaned files")

    if not orphaned_files:
        logger.info("✅ No orphaned files found!")
        return 0, 0

    # Report orphaned files
    total_size = 0
    for file_path in orphaned_files:
        try:
            size = os.path.getsize(file_path)
            total_size += size
            logger.info(f"  Orphaned: {file_path} ({size / 1024:.2f} KB)")
        except OSError as e:
            logger.warning(f"  Error getting size of {file_path}: {e}")

    logger.info(f"Total orphaned file size: {total_size / (1024 * 1024):.2f} MB")

    # Delete files if not dry run
    deleted_count = 0
    if not dry_run:
        logger.info("Deleting orphaned files...")
        for file_path in orphaned_files:
            try:
                os.remove(file_path)
                deleted_count += 1
                logger.info(f"  ✅ Deleted: {file_path}")
            except (OSError, PermissionError) as e:
                logger.error(f"  ❌ Failed to delete {file_path}: {e}")
    else:
        logger.info("DRY RUN: No files were deleted. Use --cleanup-postgresql to delete.")

    return len(orphaned_files), deleted_count


def cleanup_firebase_orphaned_files(dry_run=True):
    """
    Find and clean up orphaned files from Firebase Storage

    Args:
        dry_run: If True, only report orphaned files without deleting them

    Returns:
        Tuple of (files_found, files_deleted)
    """
    logger.info("=" * 60)
    logger.info("Scanning Firebase Storage for orphaned files...")
    logger.info("=" * 60)

    if not firebase_storage_service._initialized:
        logger.error("Firebase Storage is not initialized")
        return 0, 0

    # Get all storage paths from Firestore
    try:
        reports_ref = firestore_report_service._firestore_db.collection('reports')
        docs = reports_ref.stream()

        db_storage_paths = set()
        for doc in docs:
            report_data = doc.to_dict()
            if report_data.get('storagePath'):
                db_storage_paths.add(report_data['storagePath'])

        logger.info(f"Found {len(db_storage_paths)} expected files in Firestore")

    except Exception as e:
        logger.error(f"Error querying Firestore: {e}")
        return 0, 0

    # List all blobs in Firebase Storage reports folder
    try:
        bucket = firebase_storage_service._bucket
        blobs = bucket.list_blobs(prefix='reports/')

        orphaned_blobs = []
        total_size = 0

        for blob in blobs:
            if blob.name not in db_storage_paths:
                orphaned_blobs.append(blob)
                total_size += blob.size or 0
                logger.info(f"  Orphaned: {blob.name} ({(blob.size or 0) / 1024:.2f} KB)")

        logger.info(f"Found {len(orphaned_blobs)} orphaned files in Firebase Storage")
        logger.info(f"Total orphaned file size: {total_size / (1024 * 1024):.2f} MB")

        # Delete files if not dry run
        deleted_count = 0
        if not dry_run:
            logger.info("Deleting orphaned files from Firebase Storage...")
            for blob in orphaned_blobs:
                try:
                    blob.delete()
                    deleted_count += 1
                    logger.info(f"  ✅ Deleted: {blob.name}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to delete {blob.name}: {e}")
        else:
            logger.info("DRY RUN: No files were deleted. Use --cleanup-firebase to delete.")

        return len(orphaned_blobs), deleted_count

    except Exception as e:
        logger.error(f"Error listing Firebase Storage blobs: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0, 0


def main():
    """Main entry point for the cleanup utility"""
    parser = argparse.ArgumentParser(
        description='Cleanup orphaned files from report storage'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only report orphaned files without deleting them (default)'
    )
    parser.add_argument(
        '--cleanup-postgresql',
        action='store_true',
        help='Clean up PostgreSQL local storage orphaned files'
    )
    parser.add_argument(
        '--cleanup-firebase',
        action='store_true',
        help='Clean up Firebase Storage orphaned files'
    )

    args = parser.parse_args()

    # Default to dry run if no cleanup flags specified
    dry_run = not (args.cleanup_postgresql or args.cleanup_firebase)

    if dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN MODE - No files will be deleted")
        logger.info("=" * 60)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        logger.info(f"Cleanup started at {datetime.now()}")

        total_found = 0
        total_deleted = 0

        # Cleanup PostgreSQL files
        if args.cleanup_postgresql or dry_run:
            found, deleted = cleanup_postgresql_orphaned_files(dry_run)
            total_found += found
            total_deleted += deleted

        # Cleanup Firebase files
        if args.cleanup_firebase or dry_run:
            found, deleted = cleanup_firebase_orphaned_files(dry_run)
            total_found += found
            total_deleted += deleted

        # Summary
        logger.info("=" * 60)
        logger.info("CLEANUP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total orphaned files found: {total_found}")
        logger.info(f"Total files deleted: {total_deleted}")

        if dry_run:
            logger.info("")
            logger.info("To actually delete orphaned files, run:")
            logger.info("  python cleanup_orphaned_files.py --cleanup-postgresql --cleanup-firebase")

        logger.info(f"Cleanup completed at {datetime.now()}")


if __name__ == '__main__':
    main()
