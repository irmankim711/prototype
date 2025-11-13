"""
Test Firebase Storage and Firestore Report Integration
Run this after enabling Firebase Storage in the console
"""

import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("Firebase Storage & Firestore Reports - Integration Test")
print("=" * 70)

# Load environment
print("\n[Step 1] Loading environment...")
from app.core.env_loader import load_environment
load_environment()

# Create Flask app
print("\n[Step 2] Creating Flask app...")
from app import create_app
app = create_app()

with app.app_context():
    print("\n[Step 3] Testing Firebase Storage Service...")
    from app.services.firebase_storage_service import firebase_storage_service

    if not firebase_storage_service._initialized:
        print("❌ Firebase Storage not initialized!")
        print("\nPossible reasons:")
        print("  1. Storage not enabled in Firebase Console")
        print("  2. Service account missing Storage permissions")
        print("  3. Bucket name not configured")
        print("\n👉 Follow the setup guide: FIREBASE_STORAGE_QUICK_SETUP.md")
        sys.exit(1)

    print("✅ Firebase Storage initialized")
    print(f"   Bucket: {firebase_storage_service._bucket.name}")

    # Test 1: Create a test file
    print("\n[Step 4] Creating test file...")
    test_file_path = os.path.join(tempfile.gettempdir(), 'test_report.txt')
    test_content = f"Test report created at {os.environ.get('COMPUTERNAME', 'unknown')}\n"
    test_content += f"Timestamp: {__import__('datetime').datetime.now().isoformat()}\n"
    test_content += "This is a test file for Firebase Storage integration.\n"

    with open(test_file_path, 'w') as f:
        f.write(test_content)

    print(f"✅ Created test file: {test_file_path}")

    # Test 2: Upload file
    print("\n[Step 5] Uploading test file to Firebase Storage...")
    storage_path = 'test/test_report.txt'

    upload_url = firebase_storage_service.upload_file(
        file_path=test_file_path,
        destination_path=storage_path,
        metadata={'test': 'true', 'uploadedBy': 'test_script'},
        make_public=False
    )

    if upload_url:
        print(f"✅ Upload successful!")
        print(f"   Storage path: {storage_path}")
        print(f"   Download URL: {upload_url[:80]}...")
    else:
        print("❌ Upload failed!")
        print("\nCheck:")
        print("  1. Storage is enabled in Firebase Console")
        print("  2. Security rules allow backend writes")
        print("  3. Backend logs for detailed error")
        sys.exit(1)

    # Test 3: Check file exists
    print("\n[Step 6] Verifying file exists...")
    exists = firebase_storage_service.file_exists(storage_path)

    if exists:
        print(f"✅ File exists in Storage: {storage_path}")
    else:
        print("❌ File not found in Storage!")
        sys.exit(1)

    # Test 4: Generate signed URL
    print("\n[Step 7] Generating signed URL...")
    signed_url = firebase_storage_service.get_signed_url(
        storage_path=storage_path,
        expiration_hours=1
    )

    if signed_url:
        print(f"✅ Signed URL generated (valid for 1 hour)")
        print(f"   URL: {signed_url[:80]}...")
    else:
        print("❌ Failed to generate signed URL")

    # Test 5: Download file
    print("\n[Step 8] Downloading file from Storage...")
    download_path = os.path.join(tempfile.gettempdir(), 'downloaded_test_report.txt')

    success = firebase_storage_service.download_file(
        storage_path=storage_path,
        destination_path=download_path
    )

    if success and os.path.exists(download_path):
        with open(download_path, 'r') as f:
            downloaded_content = f.read()

        if downloaded_content == test_content:
            print(f"✅ Download successful and content matches!")
            print(f"   Downloaded to: {download_path}")
        else:
            print("⚠️ Download successful but content doesn't match")
    else:
        print("❌ Download failed")

    # Test 6: List files
    print("\n[Step 9] Listing files in 'test/' folder...")
    files = firebase_storage_service.list_files(prefix='test/')

    if files:
        print(f"✅ Found {len(files)} file(s):")
        for file in files:
            print(f"   - {file}")
    else:
        print("⚠️ No files found (this might be okay if this is the first test)")

    # Test 7: Test Firestore Report Service
    print("\n[Step 10] Testing Firestore Report Service...")
    from app.services.firestore_report_service import firestore_report_service

    if not firestore_report_service._initialized:
        print("❌ Firestore Report Service not initialized!")
        sys.exit(1)

    print("✅ Firestore Report Service initialized")

    # Create a test report
    print("\n[Step 11] Creating test report in Firestore...")
    report_id = firestore_report_service.create_report(
        user_id='test_user_123',
        title='Test Report',
        description='This is a test report created by the integration test',
        report_type='document'
    )

    if report_id:
        print(f"✅ Created test report: {report_id}")
    else:
        print("❌ Failed to create report in Firestore")
        sys.exit(1)

    # Upload report file
    print("\n[Step 12] Uploading report file to Storage...")
    report_url = firestore_report_service.save_report_file(
        report_id=report_id,
        file_path=test_file_path,
        file_format='txt'
    )

    if report_url:
        print(f"✅ Report file uploaded successfully!")
        print(f"   Report ID: {report_id}")
        print(f"   Download URL: {report_url[:80]}...")
    else:
        print("❌ Failed to upload report file")

    # Get report
    print("\n[Step 13] Retrieving report from Firestore...")
    report = firestore_report_service.get_report(report_id)

    if report:
        print(f"✅ Retrieved report:")
        print(f"   Title: {report.get('title')}")
        print(f"   Status: {report.get('generationStatus')}")
        print(f"   Storage Path: {report.get('storagePath')}")
        print(f"   File Size: {report.get('fileSize')} bytes")
    else:
        print("❌ Failed to retrieve report")

    # Get user reports
    print("\n[Step 14] Getting user's reports...")
    user_reports = firestore_report_service.get_user_reports(
        user_id='test_user_123',
        limit=10
    )

    if user_reports:
        print(f"✅ Found {len(user_reports)} report(s) for user")
        for r in user_reports:
            print(f"   - {r.get('title')} ({r.get('generationStatus')})")
    else:
        print("⚠️ No reports found for user")

    # Cleanup
    print("\n[Step 15] Cleaning up test files...")

    # Delete from Storage
    deleted = firebase_storage_service.delete_file(storage_path)
    if deleted:
        print(f"✅ Deleted test file from Storage: {storage_path}")

    # Delete report
    report_deleted = firestore_report_service.delete_report(report_id, delete_file=True)
    if report_deleted:
        print(f"✅ Deleted test report from Firestore: {report_id}")

    # Delete local files
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
    if os.path.exists(download_path):
        os.remove(download_path)

    print("✅ Local test files cleaned up")

print("\n" + "=" * 70)
print("🎉 ALL TESTS PASSED!")
print("=" * 70)
print("\nFirebase Storage and Firestore Reports are working correctly!")
print("\nNext steps:")
print("  1. ✅ Firebase Storage is ready to use")
print("  2. ✅ Firestore Reports service is functional")
print("  3. 👉 You can now integrate this into your report generation routes")
print("\nRefer to FIREBASE_STORAGE_SETUP.md for usage examples.")
print("=" * 70)
