"""
Comprehensive Report Cleanup Script
====================================
This script removes all reports from:
1. Firestore database
2. SQL database (reports table and related tables)
3. Local file storage (backend/static/previews, backend/static/generated)
4. Firebase Storage

Usage:
    python cleanup_all_reports.py --dry-run    # Preview what will be deleted
    python cleanup_all_reports.py --confirm    # Actually delete everything
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import Report

try:
    from app.models.report_models import ReportVersion, ReportEdit, ReportCollaboration, TemplateRating
    HAS_REPORT_MODELS = True
except (ImportError, Exception) as e:
    print(f"Note: Could not import report_models: {e}")
    HAS_REPORT_MODELS = False
    ReportVersion = None
    ReportEdit = None
    ReportCollaboration = None
    TemplateRating = None

from app.services.firestore_report_service import FirestoreReportService
from app.services.firebase_storage_service import FirebaseStorageService

class ReportCleanupService:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.app = create_app()
        self.stats = {
            'firestore_reports': 0,
            'sql_reports': 0,
            'sql_versions': 0,
            'sql_edits': 0,
            'sql_collaborations': 0,
            'sql_ratings': 0,
            'preview_files': 0,
            'generated_files': 0,
            'chart_files': 0,
            'export_files': 0,
            'firebase_storage_files': 0,
            'errors': []
        }

        # Initialize services
        self.firestore_service = FirestoreReportService()
        self.storage_service = FirebaseStorageService()

    def log(self, message, level='INFO'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = '[DRY RUN] ' if self.dry_run else ''
        print(f"{prefix}[{timestamp}] [{level}] {message}")

    def cleanup_firestore_reports(self):
        """Delete all reports from Firestore"""
        self.log("Starting Firestore cleanup...")

        try:
            db_firestore = firestore.client()
            reports_ref = db_firestore.collection('reports')

            # Get all reports
            reports = reports_ref.stream()

            for report in reports:
                report_id = report.id
                report_data = report.to_dict()

                self.log(f"  Found report: {report_id} - {report_data.get('title', 'Untitled')}")

                if not self.dry_run:
                    reports_ref.document(report_id).delete()
                    self.log(f"  Deleted Firestore report: {report_id}")

                self.stats['firestore_reports'] += 1

            self.log(f"Firestore cleanup complete: {self.stats['firestore_reports']} reports")

        except Exception as e:
            error_msg = f"Error cleaning Firestore: {str(e)}"
            self.log(error_msg, 'ERROR')
            self.stats['errors'].append(error_msg)

    def cleanup_sql_database(self):
        """Delete all reports from SQL database"""
        self.log("Starting SQL database cleanup...")

        with self.app.app_context():
            try:
                # Clean up related tables first (foreign key constraints)

                if HAS_REPORT_MODELS:
                    # 1. Report Versions
                    if ReportVersion:
                        versions = ReportVersion.query.all()
                        self.log(f"  Found {len(versions)} report versions")
                        for version in versions:
                            self.log(f"    Version {version.id} for report {version.report_id}")
                            if not self.dry_run:
                                db.session.delete(version)
                        self.stats['sql_versions'] = len(versions)

                    # 2. Report Edits
                    if ReportEdit:
                        edits = ReportEdit.query.all()
                        self.log(f"  Found {len(edits)} report edits")
                        for edit in edits:
                            self.log(f"    Edit {edit.id} for report {edit.report_id}")
                            if not self.dry_run:
                                db.session.delete(edit)
                        self.stats['sql_edits'] = len(edits)

                    # 3. Report Collaborations
                    if ReportCollaboration:
                        collaborations = ReportCollaboration.query.all()
                        self.log(f"  Found {len(collaborations)} report collaborations")
                        for collab in collaborations:
                            self.log(f"    Collaboration {collab.id} for report {collab.report_id}")
                            if not self.dry_run:
                                db.session.delete(collab)
                        self.stats['sql_collaborations'] = len(collaborations)

                    # 4. Template Ratings
                    if TemplateRating:
                        ratings = TemplateRating.query.all()
                        self.log(f"  Found {len(ratings)} template ratings")
                        for rating in ratings:
                            self.log(f"    Rating {rating.id} for template {rating.template_id}")
                            if not self.dry_run:
                                db.session.delete(rating)
                        self.stats['sql_ratings'] = len(ratings)
                else:
                    self.log("  Skipping related tables (report_models not available)")

                # 5. Main Reports table
                reports = Report.query.all()
                self.log(f"  Found {len(reports)} reports in SQL database")
                for report in reports:
                    self.log(f"    Report {report.id}: {report.title}")
                    if not self.dry_run:
                        db.session.delete(report)
                self.stats['sql_reports'] = len(reports)

                if not self.dry_run:
                    db.session.commit()
                    self.log("SQL database cleanup committed")

                self.log(f"SQL database cleanup complete: {self.stats['sql_reports']} reports, "
                        f"{self.stats['sql_versions']} versions, "
                        f"{self.stats['sql_edits']} edits, "
                        f"{self.stats['sql_collaborations']} collaborations, "
                        f"{self.stats['sql_ratings']} ratings")

            except Exception as e:
                error_msg = f"Error cleaning SQL database: {str(e)}"
                self.log(error_msg, 'ERROR')
                self.stats['errors'].append(error_msg)
                if not self.dry_run:
                    db.session.rollback()

    def cleanup_local_files(self):
        """Delete all report-related files from local storage"""
        self.log("Starting local file cleanup...")

        base_path = os.path.join(os.path.dirname(__file__), 'static')

        # Define directories to clean
        directories = [
            ('previews', 'preview_files'),
            ('generated/previews', 'generated_files'),
            ('charts', 'chart_files'),
            ('exports', 'export_files')
        ]

        for dir_name, stat_key in directories:
            dir_path = os.path.join(base_path, dir_name)

            if not os.path.exists(dir_path):
                self.log(f"  Directory not found: {dir_path}")
                continue

            self.log(f"  Cleaning directory: {dir_path}")

            try:
                files = os.listdir(dir_path)
                self.log(f"    Found {len(files)} files")

                for filename in files:
                    file_path = os.path.join(dir_path, filename)

                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        self.log(f"      {filename} ({file_size} bytes)")

                        if not self.dry_run:
                            os.remove(file_path)
                            self.log(f"      Deleted: {filename}")

                        self.stats[stat_key] += 1

            except Exception as e:
                error_msg = f"Error cleaning {dir_path}: {str(e)}"
                self.log(error_msg, 'ERROR')
                self.stats['errors'].append(error_msg)

        self.log(f"Local file cleanup complete: "
                f"{self.stats['preview_files']} previews, "
                f"{self.stats['generated_files']} generated files, "
                f"{self.stats['chart_files']} charts, "
                f"{self.stats['export_files']} exports")

    def cleanup_firebase_storage(self):
        """Delete all report files from Firebase Storage"""
        self.log("Starting Firebase Storage cleanup...")

        try:
            bucket = storage.bucket()

            # List all blobs in the reports/ directory
            blobs = bucket.list_blobs(prefix='reports/')

            for blob in blobs:
                self.log(f"  Found storage file: {blob.name} ({blob.size} bytes)")

                if not self.dry_run:
                    blob.delete()
                    self.log(f"  Deleted: {blob.name}")

                self.stats['firebase_storage_files'] += 1

            self.log(f"Firebase Storage cleanup complete: {self.stats['firebase_storage_files']} files")

        except Exception as e:
            error_msg = f"Error cleaning Firebase Storage: {str(e)}"
            self.log(error_msg, 'ERROR')
            self.stats['errors'].append(error_msg)

    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "="*80)
        print("CLEANUP SUMMARY")
        print("="*80)

        if self.dry_run:
            print("\n*** DRY RUN MODE - No data was actually deleted ***\n")
        else:
            print("\n*** CLEANUP COMPLETED ***\n")

        print(f"Firestore Reports:          {self.stats['firestore_reports']}")
        print(f"SQL Reports:                {self.stats['sql_reports']}")
        print(f"SQL Report Versions:        {self.stats['sql_versions']}")
        print(f"SQL Report Edits:           {self.stats['sql_edits']}")
        print(f"SQL Report Collaborations:  {self.stats['sql_collaborations']}")
        print(f"SQL Template Ratings:       {self.stats['sql_ratings']}")
        print(f"Preview Files:              {self.stats['preview_files']}")
        print(f"Generated Files:            {self.stats['generated_files']}")
        print(f"Chart Files:                {self.stats['chart_files']}")
        print(f"Export Files:               {self.stats['export_files']}")
        print(f"Firebase Storage Files:     {self.stats['firebase_storage_files']}")

        total_items = sum([
            self.stats['firestore_reports'],
            self.stats['sql_reports'],
            self.stats['sql_versions'],
            self.stats['sql_edits'],
            self.stats['sql_collaborations'],
            self.stats['sql_ratings'],
            self.stats['preview_files'],
            self.stats['generated_files'],
            self.stats['chart_files'],
            self.stats['export_files'],
            self.stats['firebase_storage_files']
        ])

        print(f"\nTotal Items:                {total_items}")

        if self.stats['errors']:
            print(f"\nErrors encountered:         {len(self.stats['errors'])}")
            print("\nError details:")
            for error in self.stats['errors']:
                print(f"  - {error}")

        print("\n" + "="*80)

    def run(self):
        """Execute the full cleanup process"""
        self.log("="*80)
        self.log("REPORT CLEANUP SCRIPT")
        self.log("="*80)

        if self.dry_run:
            self.log("Running in DRY RUN mode - no data will be deleted")
        else:
            self.log("WARNING: Running in LIVE mode - data WILL be permanently deleted!")

        self.log("")

        # Run all cleanup operations
        self.cleanup_firestore_reports()
        print()

        self.cleanup_sql_database()
        print()

        self.cleanup_local_files()
        print()

        self.cleanup_firebase_storage()
        print()

        # Print summary
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(description='Clean up all reports from the system')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                      help='Preview what will be deleted without actually deleting')
    group.add_argument('--confirm', action='store_true',
                      help='Actually delete all reports (use with caution!)')

    args = parser.parse_args()

    # Create and run cleanup service
    cleanup_service = ReportCleanupService(dry_run=args.dry_run)

    if not args.dry_run:
        print("\n" + "!"*80)
        print("WARNING: You are about to PERMANENTLY DELETE all reports!")
        print("!"*80)
        print("\nThis will delete:")
        print("  - All Firestore report documents")
        print("  - All SQL database report records")
        print("  - All local report files")
        print("  - All Firebase Storage report files")
        print("\nThis action CANNOT be undone!")
        print("\n" + "!"*80 + "\n")

        response = input("Type 'DELETE ALL REPORTS' to confirm: ")

        if response != 'DELETE ALL REPORTS':
            print("\nCleanup cancelled.")
            return

        print("\nProceeding with cleanup...\n")

    cleanup_service.run()


if __name__ == '__main__':
    main()
