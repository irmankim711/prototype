"""
Quick test of Firebase Reports API
Tests the generate-sample endpoint which creates a report in Firebase Storage
"""
import sys
import os

# Load environment
sys.path.insert(0, os.path.dirname(__file__))
from app.core.env_loader import load_environment
load_environment()

from app import create_app

print("=" * 70)
print("Testing Firebase Reports API - Generate Sample Report")
print("=" * 70)

app = create_app()

with app.app_context():
    from app.middleware.firebase_auth import firebase_auth_manager
    from flask import g

    print(f"\n✅ Firebase Storage initialized: {firebase_auth_manager._initialized}")

    # Create a test user
    test_token_data = {
        'uid': 'test-reports-uid-789',
        'email': 'reporttest@example.com',
        'name': 'Report Tester'
    }

    print(f"\n[Step 1] Creating test user...")
    user = firebase_auth_manager.get_or_create_user(test_token_data)

    if not user:
        print("❌ Failed to create user")
        sys.exit(1)

    user_id = user.get('id') if isinstance(user, dict) else user.id
    print(f"✅ User created: {user.get('email') if isinstance(user, dict) else user.email}")

    # Test the generate-sample endpoint
    print(f"\n[Step 2] Generating sample report...")

    with app.test_request_context(
        '/api/firebase-reports/generate-sample',
        method='POST',
        json={'title': 'Test Cloud Report'},
        headers={'Authorization': 'Bearer fake-test-token'}
    ):
        # Set user context
        g.current_user = user
        g.current_user_id = user_id
        g.firebase_token = test_token_data
        g.firebase_uid = test_token_data.get('uid')

        # Call the endpoint
        from app.routes.firebase_reports_api import generate_sample_report

        try:
            response = generate_sample_report()

            if isinstance(response, tuple):
                response_data, status_code = response
                response_json = response_data.get_json()
            else:
                response_json = response.get_json()
                status_code = 200

            print(f"\n[Step 3] Response:")
            print(f"   Status: {status_code}")
            print(f"   Success: {response_json.get('success')}")

            if response_json.get('success'):
                print(f"\n✅ REPORT GENERATED SUCCESSFULLY!")
                print(f"   Report ID: {response_json.get('reportId')}")
                print(f"   Title: {response_json.get('report', {}).get('title')}")
                print(f"   Status: {response_json.get('report', {}).get('generationStatus')}")
                print(f"   Download URL: {response_json.get('downloadUrl')[:80]}...")
                print(f"\n🎉 Your first report is now stored in Firebase Storage!")
                print(f"   Check Firebase Console → Storage to see the file")
                print(f"   Check Firestore → reports collection to see metadata")
            else:
                print(f"\n❌ Failed: {response_json.get('error')}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)
