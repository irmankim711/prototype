"""
Migration script to fix existing Firestore reports that have SQL user IDs
instead of Firebase UIDs in createdBy.userId field.

This fixes the 403 error when downloading old reports.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.firestore_report_service import firestore_report_service
from app.models import User
from app import create_app

def migrate_report_ownership():
    """Update all reports with SQL user IDs to use Firebase UIDs"""

    print("🔄 Starting Firestore report ownership migration...")

    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Get all reports from Firestore
        reports = firestore_report_service._firestore_db.collection('reports').stream()

        updated_count = 0
        skipped_count = 0
        error_count = 0

        for doc in reports:
            report_id = doc.id
            report_data = doc.to_dict()

            created_by = report_data.get('createdBy', {})
            current_user_id = created_by.get('userId')

            if not current_user_id:
                print(f"⚠️  Report {report_id}: No userId found, skipping")
                skipped_count += 1
                continue

            # Check if it's already a Firebase UID (contains letters) or SQL ID (only digits)
            if not str(current_user_id).isdigit():
                print(f"✓  Report {report_id}: Already using Firebase UID ({current_user_id}), skipping")
                skipped_count += 1
                continue

            # It's a SQL user ID, need to convert to Firebase UID
            try:
                # Query User table to get Firebase UID
                user = User.query.get(int(current_user_id))

                if not user:
                    print(f"❌ Report {report_id}: User {current_user_id} not found in database")
                    error_count += 1
                    continue

                if not user.firebase_uid:
                    print(f"❌ Report {report_id}: User {current_user_id} has no Firebase UID")
                    error_count += 1
                    continue

                # Update the report with Firebase UID
                doc_ref = firestore_report_service._firestore_db.collection('reports').document(report_id)
                doc_ref.update({
                    'createdBy.userId': user.firebase_uid
                })

                print(f"✅ Report {report_id}: Updated userId from '{current_user_id}' to '{user.firebase_uid}'")
                updated_count += 1

            except Exception as e:
                print(f"❌ Report {report_id}: Error updating - {str(e)}")
                error_count += 1

    print("\n" + "="*60)
    print("Migration Summary:")
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ⏭️  Skipped: {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    print("="*60)

    if updated_count > 0:
        print("\n✨ Migration completed! Old reports should now be downloadable.")
    elif skipped_count > 0:
        print("\n✨ All reports already use Firebase UIDs. No migration needed.")
    else:
        print("\n⚠️  No reports were migrated. Check for errors above.")

if __name__ == '__main__':
    try:
        migrate_report_ownership()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
