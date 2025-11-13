"""
Test profile endpoint with Firebase authentication
"""
import sys
import os
import requests
import json

# Test configuration
BASE_URL = "http://127.0.0.1:5000"

print("=" * 70)
print("Testing Profile Endpoint with Firebase Authentication")
print("=" * 70)

# Step 1: Create a fake Firebase token (for testing, you'll need a real one from frontend)
print("\n[Step 1] Note: For this test to work with a real Firebase token,")
print("         you need to get an ID token from the frontend after logging in.")
print("         For now, let's test with our test Firebase flow instead.\n")

# Load environment and create test token
sys.path.insert(0, os.path.dirname(__file__))

from app.core.env_loader import load_environment
load_environment()

from app import create_app
app = create_app()

with app.app_context():
    from app.middleware.firebase_auth import firebase_auth_manager

    print(f"Firebase initialized: {firebase_auth_manager._initialized}")
    print(f"Firestore available: {firebase_auth_manager._firestore_db is not None}")

    if not firebase_auth_manager._initialized:
        print("❌ Firebase not initialized! Cannot proceed with test.")
        sys.exit(1)

    # Create or get a test user
    test_token_data = {
        'uid': 'test-profile-uid-456',
        'email': 'profiletest@example.com',
        'name': 'Profile Tester'
    }

    print(f"\n[Step 2] Creating/getting test user...")
    user = firebase_auth_manager.get_or_create_user(test_token_data)

    if not user:
        print("❌ Failed to create/get user")
        sys.exit(1)

    if isinstance(user, dict):
        print(f"✅ User retrieved from Firestore")
        print(f"   Email: {user.get('email')}")
        print(f"   ID: {user.get('id')}")
        print(f"   Role: {user.get('role')}")
    else:
        print(f"✅ User retrieved from SQLite")
        print(f"   Email: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Role: {user.role}")

    # Now we need to generate a real Firebase ID token for testing
    # For testing purposes, let's simulate the request handling
    print(f"\n[Step 3] Simulating profile endpoint request...")

    from flask import g
    from app.decorators import firebase_auth_required

    # Create a mock request context
    with app.test_request_context(
        '/api/users/profile',
        method='GET',
        headers={'Authorization': f'Bearer fake-token-for-test'}
    ):
        # Manually set the user in g (simulating what @require_auth does)
        g.current_user = user
        g.current_user_id = user.get('id') if isinstance(user, dict) else user.id
        g.firebase_token = test_token_data
        g.firebase_uid = test_token_data.get('uid')

        # Import and call the profile endpoint function
        from app.routes.enhanced_user_routes import get_user_profile

        try:
            response = get_user_profile()

            # Check if response is a tuple (response, status_code) or just response
            if isinstance(response, tuple):
                response_data, status_code = response
                response_json = response_data.get_json()
            else:
                response_json = response.get_json()
                status_code = 200

            print(f"\n[Step 4] Profile endpoint response:")
            print(f"   Status code: {status_code}")
            print(f"   Response: {json.dumps(response_json, indent=2)}")

            if status_code == 200 and response_json.get('success'):
                print(f"\n✅ Profile endpoint working correctly!")
                print(f"   Retrieved user: {response_json.get('user', {}).get('email')}")
            else:
                print(f"\n❌ Profile endpoint returned error")

        except Exception as e:
            print(f"\n❌ Error calling profile endpoint: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)
