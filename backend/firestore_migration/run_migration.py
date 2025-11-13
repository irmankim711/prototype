"""
Custom Migration Script for Your System
========================================

This script is configured specifically for your database setup.
It uses your existing SQLite database and Firebase credentials.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from app
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import the migration class
from firestore_migration.migrate_sql_to_firestore import FirestoreMigration

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')


def main():
    print("=" * 80)
    print("FIRESTORE MIGRATION SCRIPT")
    print("=" * 80)
    print()

    # Configuration from your .env file
    sqlite_db_path = "C:/Users/IRMAN/OneDrive/Desktop/prototype/backend/app.db"
    firebase_cred_path = "C:/Users/IRMAN/OneDrive/Desktop/prototype/backend/service/report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json"

    # Construct SQLite connection string
    sql_connection_string = f"sqlite:///{sqlite_db_path}"

    print(f"📊 Database: {sqlite_db_path}")
    print(f"🔥 Firebase Project: report-automation-57f6e")
    print(f"🔑 Credentials: {firebase_cred_path}")
    print()

    # Check if files exist
    if not os.path.exists(sqlite_db_path):
        print(f"❌ ERROR: SQLite database not found at {sqlite_db_path}")
        return

    if not os.path.exists(firebase_cred_path):
        print(f"❌ ERROR: Firebase credentials not found at {firebase_cred_path}")
        return

    print("✅ All required files found")
    print()

    # Ask user for confirmation
    mode = input("Choose migration mode (test/full) [test]: ").strip().lower() or "test"

    if mode not in ['test', 'full']:
        print("❌ Invalid mode. Please choose 'test' or 'full'")
        return

    print()
    print(f"🚀 Starting {mode.upper()} migration...")
    print()

    if mode == "full":
        confirm = input("⚠️  This will migrate ALL data to Firestore. Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Migration cancelled")
            return

    try:
        # Initialize migration
        migration = FirestoreMigration(sql_connection_string, firebase_cred_path)

        if mode == 'test':
            print("🧪 Running TEST migration (first 10 records only)...")
            print()

            # Migrate limited data for testing
            migration.migrate_users(batch_size=10)
            migration.migrate_forms(batch_size=10)

            print()
            print("✅ TEST MIGRATION COMPLETED!")
            print()
            print("📊 Migration Statistics:")
            print(f"   Users: {migration.stats['users']}")
            print(f"   Forms: {migration.stats['forms']}")
            print()
            print("🔍 Next Steps:")
            print("   1. Check Firebase Console to verify data")
            print("   2. Go to: https://console.firebase.google.com/project/report-automation-57f6e/firestore")
            print("   3. If everything looks good, run with mode='full'")

        else:
            print("🔄 Running FULL migration...")
            print("⏳ This may take several minutes depending on data size...")
            print()

            # Run complete migration
            migration.run_full_migration()

            print()
            print("✅ FULL MIGRATION COMPLETED!")
            print()
            print("📊 Final Migration Statistics:")
            print(f"   Users: {migration.stats['users']}")
            print(f"   Forms: {migration.stats['forms']}")
            print(f"   Programs: {migration.stats['programs']}")
            print(f"   Reports: {migration.stats['reports']}")
            print()
            print("🎉 Your data is now in Firestore!")
            print("🔍 View in Firebase Console:")
            print("   https://console.firebase.google.com/project/report-automation-57f6e/firestore")

    except Exception as e:
        print()
        print("❌ MIGRATION FAILED!")
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
