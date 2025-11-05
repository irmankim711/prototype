"""
Firestore Migration: Create ParsedExcelFiles and ExcelTables Collections
Simplified version that just creates the collections without migrating existing data
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
env_path = backend_dir / '.env'
if env_path.exists():
    print(f"📁 Loading environment from: {env_path}")
    load_dotenv(env_path)

# Set GOOGLE_APPLICATION_CREDENTIALS
firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
if firebase_service_account:
    credentials_path = backend_dir / firebase_service_account
    if credentials_path.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
        print(f"✅ Using Firebase credentials: {credentials_path.name}")

from app.middleware.firebase_auth import firebase_auth_manager


def create_firestore_collections():
    """
    Create Firestore collections for multi-file Excel support
    """
    print("\n" + "=" * 60)
    print("FIRESTORE SETUP: Excel File Tracking")
    print("=" * 60)

    # Check Firebase initialization
    if not firebase_auth_manager._initialized:
        print("❌ Firebase not initialized")
        print("\n💡 To fix this:")
        print("   1. Check that FIREBASE_SERVICE_ACCOUNT_PATH is set in .env")
        print("   2. Verify the service account JSON file exists")
        print("   3. Check Firebase credentials are valid")
        return False

    firestore_db = firebase_auth_manager._firestore_db
    if not firestore_db:
        print("❌ Firestore database not available")
        return False

    print("✅ Firebase initialized successfully\n")

    # Get collections
    parsed_files_collection = firestore_db.collection('parsed_excel_files')
    excel_tables_collection = firestore_db.collection('excel_tables')

    print("📁 Creating Firestore Collections:")
    print("   1. parsed_excel_files")
    print("   2. excel_tables\n")

    # Create sample document to initialize collection (will be deleted)
    try:
        # Create test document in parsed_excel_files
        test_file_ref = parsed_files_collection.document('_test_init')
        test_file_ref.set({
            'id': '_test_init',
            'user_id': 'system',
            'original_filename': 'test.xlsx',
            'file_path': '/test/path',
            'file_size': 0,
            'status': 'test',
            'uploaded_at': datetime.utcnow(),
            'tables_count': 0,
            'total_rows': 0,
            'total_columns': 0,
            'sheets_processed': 0,
            'metadata': {},
            'created_at': datetime.utcnow()
        })
        print("   ✅ Created parsed_excel_files collection")

        # Create test document in excel_tables
        test_table_ref = excel_tables_collection.document('_test_init')
        test_table_ref.set({
            'id': '_test_init',
            'parsed_file_id': '_test_init',
            'name': 'Test Table',
            'sheet_name': 'Sheet1',
            'row_count': 0,
            'column_count': 0,
            'headers': [],
            'data_types': [],
            'table_range': 'A1:A1',
            'has_data': False,
            'created_at': datetime.utcnow()
        })
        print("   ✅ Created excel_tables collection")

        # Delete test documents
        test_file_ref.delete()
        test_table_ref.delete()
        print("   ✅ Cleaned up test documents\n")

    except Exception as e:
        print(f"   ❌ Error creating collections: {e}\n")
        return False

    print("📋 Next Steps:")
    print("   1. Deploy Firestore indexes:")
    print("      firebase deploy --only firestore:indexes\n")
    print("   2. Deploy Firestore security rules:")
    print("      firebase deploy --only firestore:rules\n")
    print("   3. Test file upload via API\n")

    print("=" * 60)
    print("✅ Firestore collections created successfully!")
    print("=" * 60)

    return True


def show_firestore_rules():
    """Display the Firestore security rules"""
    print("\n" + "=" * 60)
    print("FIRESTORE SECURITY RULES")
    print("=" * 60)
    print("""
Save these rules to firestore.rules and deploy with:
firebase deploy --only firestore:rules

rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // ParsedExcelFiles - user can only access their own files
    match /parsed_excel_files/{fileId} {
      allow read, write: if request.auth != null
                         && request.auth.uid == resource.data.user_id;
    }

    // ExcelTables - user can access if they own parent file
    match /excel_tables/{tableId} {
      allow read: if request.auth != null
                  && exists(/databases/$(database)/documents/parsed_excel_files/$(resource.data.parsed_file_id))
                  && get(/databases/$(database)/documents/parsed_excel_files/$(resource.data.parsed_file_id)).data.user_id == request.auth.uid;
    }
  }
}
""")


if __name__ == '__main__':
    print("\n🚀 Starting Firestore Setup...")
    print(f"📅 Date: {datetime.now().isoformat()}\n")

    success = create_firestore_collections()

    if success:
        show_firestore_rules()
        print("\n✅ Setup complete! Firestore is ready for multi-file Excel support.\n")
    else:
        print("\n❌ Setup failed. Please check the errors above.\n")
        sys.exit(1)
