"""
Firestore Migration: Add ParsedExcelFiles and ExcelTables Collections
Created: 2025-01-05
Purpose: Enable multi-file Excel support in Firestore for cross-platform access
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = backend_dir / '.env'
if env_path.exists():
    print(f"📁 Loading environment from: {env_path}")
    load_dotenv(env_path)
else:
    print(f"⚠️  .env file not found at: {env_path}")

# Set GOOGLE_APPLICATION_CREDENTIALS if FIREBASE_SERVICE_ACCOUNT_PATH is set
firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
if firebase_service_account and not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    credentials_path = backend_dir / firebase_service_account
    if credentials_path.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
        print(f"✅ Using Firebase credentials from: {credentials_path}")
    else:
        print(f"⚠️  Firebase service account file not found: {credentials_path}")

from app.middleware.firebase_auth import firebase_auth_manager


def migrate_parsed_excel_files():
    """
    Create ParsedExcelFiles collection in Firestore
    Migrates existing SQL records to Firestore for cross-platform access
    """
    print("=" * 60)
    print("FIRESTORE MIGRATION: ParsedExcelFiles Collection")
    print("=" * 60)

    # Initialize Firebase
    if not firebase_auth_manager._initialized:
        print("❌ Firebase not initialized. Please check your configuration.")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        print("❌ Firestore database not available.")
        return False

    print("✅ Firebase initialized successfully")

    # Get collections
    parsed_files_collection = firestore_db.collection('parsed_excel_files')
    excel_tables_collection = firestore_db.collection('excel_tables')

    print(f"\n📁 Collections:")
    print(f"   - parsed_excel_files")
    print(f"   - excel_tables")

    # Migrate existing SQL data to Firestore
    print(f"\n🔄 Migrating existing SQL data to Firestore...")

    try:
        # Import models directly from models.py to avoid circular import
        import importlib.util
        models_path = backend_dir / 'app' / 'models.py'

        spec = importlib.util.spec_from_file_location("app_models", models_path)
        app_models = importlib.util.module_from_spec(spec)

        # Set up the necessary imports for models.py
        sys.modules['app'] = type(sys)('app')
        sys.modules['app'].db = None  # Will be set below

        # Import db first
        from app import create_app, db as flask_db
        app = create_app()
        sys.modules['app'].db = flask_db

        # Now load the models
        with app.app_context():
            spec.loader.exec_module(app_models)

            ParsedExcelFile = app_models.ParsedExcelFile
            ExcelTable = app_models.ExcelTable

        # Get all parsed Excel files from SQL database
        sql_files = ParsedExcelFile.query.all()
        print(f"\n📊 Found {len(sql_files)} files in SQL database")

        migrated_count = 0
        error_count = 0

        for sql_file in sql_files:
            try:
                # Check if already exists in Firestore
                existing = parsed_files_collection.document(sql_file.id).get()

                if existing.exists:
                    print(f"   ⏭️  Skipping {sql_file.original_filename} (already in Firestore)")
                    continue

                # Create Firestore document
                file_data = {
                    'id': sql_file.id,
                    'user_id': sql_file.user_id,
                    'original_filename': sql_file.original_filename,
                    'file_path': sql_file.file_path,
                    'file_size': sql_file.file_size,
                    'status': sql_file.status,
                    'uploaded_at': sql_file.uploaded_at,
                    'tables_count': sql_file.tables_count,
                    'total_rows': sql_file.total_rows,
                    'total_columns': sql_file.total_columns,
                    'sheets_processed': sql_file.sheets_processed,
                    'metadata': sql_file.metadata or {},
                    'error_message': sql_file.error_message,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }

                # Save to Firestore
                parsed_files_collection.document(sql_file.id).set(file_data)

                # Migrate associated tables
                sql_tables = ExcelTable.query.filter_by(parsed_file_id=sql_file.id).all()

                for sql_table in sql_tables:
                    table_data = {
                        'id': sql_table.id,
                        'parsed_file_id': sql_table.parsed_file_id,
                        'name': sql_table.name,
                        'sheet_name': sql_table.sheet_name,
                        'row_count': sql_table.row_count,
                        'column_count': sql_table.column_count,
                        'headers': sql_table.headers,
                        'data_types': sql_table.data_types,
                        'table_range': sql_table.table_range,
                        'has_data': sql_table.data is not None,
                        # Note: Don't migrate full data to Firestore (can be large)
                        # Data remains in SQL for now
                        'created_at': sql_table.created_at or datetime.utcnow()
                    }

                    excel_tables_collection.document(sql_table.id).set(table_data)

                print(f"   ✅ Migrated: {sql_file.original_filename} ({len(sql_tables)} tables)")
                migrated_count += 1

            except Exception as e:
                print(f"   ❌ Error migrating {sql_file.original_filename}: {str(e)}")
                error_count += 1

        print(f"\n✅ Migration complete:")
        print(f"   - Migrated: {migrated_count} files")
        print(f"   - Errors: {error_count}")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

    # Create indexes for common queries
    print(f"\n🔧 Creating Firestore indexes...")
    print(f"   NOTE: Indexes must be created via Firebase Console or gcloud CLI")
    print(f"   Required composite indexes:")
    print(f"   1. Collection: parsed_excel_files")
    print(f"      - user_id (Ascending)")
    print(f"      - uploaded_at (Descending)")
    print(f"   2. Collection: parsed_excel_files")
    print(f"      - user_id (Ascending)")
    print(f"      - status (Ascending)")
    print(f"      - uploaded_at (Descending)")

    print(f"\n📝 To create indexes, run:")
    print(f"   firebase deploy --only firestore:indexes")

    print(f"\n✅ Firestore migration completed successfully!")
    return True


def verify_migration():
    """Verify that the migration was successful"""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        print("❌ Firestore database not available.")
        return False

    parsed_files_collection = firestore_db.collection('parsed_excel_files')
    excel_tables_collection = firestore_db.collection('excel_tables')

    # Count documents
    files_count = len(list(parsed_files_collection.limit(1000).stream()))
    tables_count = len(list(excel_tables_collection.limit(1000).stream()))

    print(f"\n📊 Firestore Document Counts:")
    print(f"   - parsed_excel_files: {files_count}")
    print(f"   - excel_tables: {tables_count}")

    # Show sample documents
    print(f"\n📄 Sample Documents:")
    sample_files = list(parsed_files_collection.limit(3).stream())

    for file_doc in sample_files:
        file_data = file_doc.to_dict()
        print(f"\n   File ID: {file_data.get('id')}")
        print(f"   Filename: {file_data.get('original_filename')}")
        print(f"   User: {file_data.get('user_id')}")
        print(f"   Status: {file_data.get('status')}")
        print(f"   Tables: {file_data.get('tables_count')}")
        print(f"   Rows: {file_data.get('total_rows')}")

    return True


def create_firestore_rules():
    """Generate Firestore security rules for Excel files"""
    print("\n" + "=" * 60)
    print("FIRESTORE SECURITY RULES")
    print("=" * 60)

    rules = """
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // ParsedExcelFiles collection - user can only access their own files
    match /parsed_excel_files/{fileId} {
      // Read: User must be authenticated and match user_id
      allow read: if request.auth != null
                  && request.auth.uid == resource.data.user_id;

      // Create: User must be authenticated and set correct user_id
      allow create: if request.auth != null
                    && request.auth.uid == request.resource.data.user_id;

      // Update: User must own the file
      allow update: if request.auth != null
                    && request.auth.uid == resource.data.user_id;

      // Delete: User must own the file
      allow delete: if request.auth != null
                    && request.auth.uid == resource.data.user_id;
    }

    // ExcelTables collection - user can access if they own the parent file
    match /excel_tables/{tableId} {
      // Read: User must own the parent file
      allow read: if request.auth != null
                  && exists(/databases/$(database)/documents/parsed_excel_files/$(resource.data.parsed_file_id))
                  && get(/databases/$(database)/documents/parsed_excel_files/$(resource.data.parsed_file_id)).data.user_id == request.auth.uid;

      // Create: System only (via backend)
      allow create: if false;

      // Update/Delete: System only (via backend)
      allow update, delete: if false;
    }
  }
}
"""

    print(rules)
    print("\n📝 Save these rules to firestore.rules and deploy with:")
    print("   firebase deploy --only firestore:rules")

    return rules


if __name__ == '__main__':
    print("\n🚀 Starting Firestore Excel Migration...")
    print(f"📅 Date: {datetime.now().isoformat()}")

    # Run migration
    success = migrate_parsed_excel_files()

    if success:
        # Verify migration
        verify_migration()

        # Show security rules
        create_firestore_rules()

        print("\n" + "=" * 60)
        print("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("   1. Deploy Firestore indexes: firebase deploy --only firestore:indexes")
        print("   2. Deploy Firestore rules: firebase deploy --only firestore:rules")
        print("   3. Test file upload and retrieval via API")
        print("   4. Verify data synchronization between SQL and Firestore")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
