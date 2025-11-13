"""
Migrate existing reports to use createdBy.userId structure
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

def migrate_reports():
    """Migrate reports from userId to createdBy.userId structure"""

    # Initialize Firebase Admin
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), 'service', 'report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Get all reports
    reports_ref = db.collection('reports')
    reports = reports_ref.stream()

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for report in reports:
        try:
            report_data = report.to_dict()
            report_id = report.id

            # Check if report already has new structure
            if 'createdBy' in report_data and isinstance(report_data['createdBy'], dict):
                print(f"✓ Skipping {report_id} - already migrated")
                skipped_count += 1
                continue

            # Check if report has old structure
            if 'userId' not in report_data:
                print(f"⚠ Warning: {report_id} has no userId field")
                skipped_count += 1
                continue

            # Migrate to new structure
            user_id = report_data['userId']
            created_at = report_data.get('createdAt', datetime.utcnow())

            # Update the document
            report.reference.update({
                'createdBy': {
                    'userId': user_id,
                    'createdAt': created_at
                }
            })

            # Optionally remove old userId field (commented out for safety)
            # report.reference.update({'userId': firestore.DELETE_FIELD})

            print(f"✓ Migrated report {report_id} for user {user_id}")
            migrated_count += 1

        except Exception as e:
            print(f"✗ Error migrating report {report_id}: {e}")
            error_count += 1

    print(f"\n{'='*50}")
    print(f"Migration Summary:")
    print(f"  Migrated: {migrated_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"  Errors:   {error_count}")
    print(f"{'='*50}")

if __name__ == '__main__':
    print("Starting report structure migration...")
    migrate_reports()
    print("Migration complete!")
