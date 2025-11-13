"""
Test Database and Firebase Connections
=======================================

This script tests your SQLite database and Firebase connections
before running the full migration.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

print("=" * 80)
print("CONNECTION TEST SCRIPT")
print("=" * 80)
print()

# Configuration
sqlite_db_path = "C:/Users/IRMAN/OneDrive/Desktop/prototype/backend/app.db"
firebase_cred_path = "C:/Users/IRMAN/OneDrive/Desktop/prototype/backend/service/report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json"

# Test 1: Check if files exist
print("📁 Test 1: Checking file existence...")
print()

if os.path.exists(sqlite_db_path):
    size_mb = os.path.getsize(sqlite_db_path) / (1024 * 1024)
    print(f"✅ SQLite database found: {sqlite_db_path}")
    print(f"   Size: {size_mb:.2f} MB")
else:
    print(f"❌ SQLite database NOT found: {sqlite_db_path}")
    sys.exit(1)

if os.path.exists(firebase_cred_path):
    print(f"✅ Firebase credentials found: {firebase_cred_path}")
else:
    print(f"❌ Firebase credentials NOT found: {firebase_cred_path}")
    sys.exit(1)

print()

# Test 2: Test SQLite connection
print("📊 Test 2: Testing SQLite database connection...")
print()

try:
    from sqlalchemy import create_engine, text, MetaData

    sql_connection_string = f"sqlite:///{sqlite_db_path}"
    engine = create_engine(sql_connection_string)

    # Test connection and get table count
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]

    print(f"✅ Database connection successful!")
    print(f"   Found {len(tables)} tables:")
    for table in tables:
        print(f"   - {table}")

    # Get row counts for main tables
    print()
    print("📊 Data counts:")
    metadata = MetaData()
    metadata.reflect(bind=engine)

    important_tables = ['user', 'forms', 'form_submissions', 'programs', 'participants']

    with engine.connect() as conn:
        for table_name in important_tables:
            if table_name in metadata.tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"   {table_name}: {count} records")

except Exception as e:
    print(f"❌ Database connection failed!")
    print(f"Error: {str(e)}")
    sys.exit(1)

print()

# Test 3: Test Firebase connection
print("🔥 Test 3: Testing Firebase connection...")
print()

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    # Initialize Firebase (if not already initialized)
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)

    # Get Firestore client
    db = firestore.client()

    # Try to read from Firestore
    # This will fail if permissions are incorrect
    collections = db.collections()
    collection_names = [col.id for col in collections]

    print(f"✅ Firebase connection successful!")
    print(f"   Project: report-automation-57f6e")

    if collection_names:
        print(f"   Existing collections: {', '.join(collection_names)}")
    else:
        print(f"   No existing collections (empty Firestore)")

except Exception as e:
    print(f"❌ Firebase connection failed!")
    print(f"Error: {str(e)}")
    print()
    print("Troubleshooting:")
    print("1. Check if the service account JSON is valid")
    print("2. Verify Firestore is enabled in Firebase Console")
    print("3. Check if service account has Firestore permissions")
    sys.exit(1)

print()

# Test 4: Check if data already exists in Firestore
print("🔍 Test 4: Checking for existing data in Firestore...")
print()

try:
    # Check main collections
    collections_to_check = ['users', 'forms', 'programs', 'reports']

    for collection_name in collections_to_check:
        docs = db.collection(collection_name).limit(1).stream()
        doc_count = len(list(docs))

        if doc_count > 0:
            print(f"⚠️  Collection '{collection_name}' already has data")
        else:
            print(f"✅ Collection '{collection_name}' is empty")

except Exception as e:
    print(f"⚠️  Could not check existing data: {str(e)}")

print()
print("=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print()
print("You are ready to run the migration!")
print()
print("Next steps:")
print("1. Run test migration:")
print("   python firestore_migration/run_migration.py")
print("   (Choose 'test' mode when prompted)")
print()
print("2. Check Firebase Console:")
print("   https://console.firebase.google.com/project/report-automation-57f6e/firestore")
print()
print("3. If test looks good, run full migration:")
print("   python firestore_migration/run_migration.py")
print("   (Choose 'full' mode when prompted)")
print()
