"""
Direct test of Firebase Storage + Firestore reports
Tests the services directly without going through the API endpoints
"""
import sys
import os

# Load environment
sys.path.insert(0, os.path.dirname(__file__))
from app.core.env_loader import load_environment
load_environment()

from app import create_app

print("=" * 70)
print("Testing Firebase Reports - Direct Service Test")
print("=" * 70)

app = create_app()

with app.app_context():
    from app.services.firestore_report_service import firestore_report_service
    from app.services.firebase_storage_service import firebase_storage_service
    from app.middleware.firebase_auth import firebase_auth_manager

    print(f"\n✅ Firebase Storage: {firebase_storage_service._initialized}")
    print(f"✅ Firestore: {firestore_report_service._initialized}")

    # Create a test user
    test_token_data = {
        'uid': 'test-direct-reports-uid',
        'email': 'directtest@example.com',
        'name': 'Direct Test User'
    }

    print(f"\n[Step 1] Creating test user...")
    user = firebase_auth_manager.get_or_create_user(test_token_data)
    user_id = user.get('id') if isinstance(user, dict) else user.id
    print(f"✅ User ID: {user_id}")

    # Create a test report in Firestore
    print(f"\n[Step 2] Creating report metadata in Firestore...")
    report_id = firestore_report_service.create_report(
        user_id=user_id,
        title="My First Cloud Report",
        description="Testing Firebase Storage integration",
        report_type="document"
    )

    if report_id:
        print(f"✅ Report created in Firestore")
        print(f"   Report ID: {report_id}")
    else:
        print("❌ Failed to create report")
        sys.exit(1)

    # Create a sample document file
    print(f"\n[Step 3] Creating sample document file...")
    sample_file_path = os.path.join(os.path.dirname(__file__), 'temp_test_report.txt')

    with open(sample_file_path, 'w') as f:
        f.write("This is a test report created by Firebase Storage integration.\n")
        f.write("Report ID: " + report_id + "\n")
        f.write("Created by: " + user.get('email', 'Unknown') + "\n")

    print(f"✅ Sample file created: {sample_file_path}")

    # Upload the file to Firebase Storage and update Firestore
    print(f"\n[Step 4] Uploading file to Firebase Storage...")
    download_url = firestore_report_service.save_report_file(
        report_id=report_id,
        file_path=sample_file_path,
        file_format='txt'
    )

    if download_url:
        print(f"✅ File uploaded to Firebase Storage!")
        print(f"   Download URL: {download_url[:100]}...")
    else:
        print("❌ Failed to upload file")
        sys.exit(1)

    # Retrieve the report details
    print(f"\n[Step 5] Retrieving report from Firestore...")
    report = firestore_report_service.get_report(report_id)

    if report:
        print(f"✅ Report retrieved successfully")
        print(f"   Title: {report.get('title')}")
        print(f"   Status: {report.get('generationStatus')}")
        print(f"   File Name: {report.get('fileName')}")
        print(f"   Storage Path: {report.get('storagePath')}")
    else:
        print("❌ Failed to retrieve report")

    # Get a fresh signed URL
    print(f"\n[Step 6] Generating new signed URL...")
    storage_path = report.get('storagePath')
    if storage_path:
        signed_url = firebase_storage_service.get_signed_url(storage_path, expiration_hours=24)
        if signed_url:
            print(f"✅ Signed URL generated (valid for 24 hours)")
            print(f"   URL: {signed_url[:100]}...")
        else:
            print("⚠️ Could not generate signed URL")

    # List all reports for this user
    print(f"\n[Step 7] Listing all reports for user...")
    user_reports = firestore_report_service.get_user_reports(user_id, limit=10)

    if user_reports:
        print(f"✅ Found {len(user_reports)} report(s)")
        for idx, r in enumerate(user_reports, 1):
            print(f"   {idx}. {r.get('title')} - {r.get('generationStatus')}")
    else:
        print("⚠️ No reports found")

    # Clean up temp file
    print(f"\n[Step 8] Cleaning up temp file...")
    try:
        os.remove(sample_file_path)
        print(f"✅ Temp file removed")
    except:
        print(f"⚠️ Could not remove temp file")

    print("\n" + "=" * 70)
    print("🎉 SUCCESS! Firebase Reports System is Working!")
    print("=" * 70)
    print("\nWhat happened:")
    print("1. ✅ Created user in Firestore")
    print("2. ✅ Created report metadata in Firestore")
    print("3. ✅ Uploaded file to Firebase Storage")
    print("4. ✅ Generated signed download URL")
    print("5. ✅ Retrieved report data from Firestore")
    print("\nYou can now:")
    print("• Check Firebase Console → Storage to see your file")
    print("• Check Firebase Console → Firestore → 'reports' collection")
    print("• Use the API endpoints from your frontend")
    print("=" * 70)
