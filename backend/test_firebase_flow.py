"""
Test Firebase authentication flow
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment first
print("=" * 60)
print("Step 1: Loading environment")
print("=" * 60)
from app.core.env_loader import load_environment
load_environment()

service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
print(f"✅ FIREBASE_SERVICE_ACCOUNT_PATH: {service_account_path}")

# Create Flask app
print("\n" + "=" * 60)
print("Step 2: Creating Flask app")
print("=" * 60)
from app import create_app
app = create_app()

# Test Firebase auth manager
print("\n" + "=" * 60)
print("Step 3: Testing Firebase auth manager")
print("=" * 60)
with app.app_context():
    from app.middleware.firebase_auth import firebase_auth_manager

    print(f"Firebase initialized: {firebase_auth_manager._initialized}")
    print(f"Initialization attempts: {firebase_auth_manager._initialization_attempts}")

    if firebase_auth_manager._initialization_error:
        print(f"❌ Initialization error: {firebase_auth_manager._initialization_error}")

    if firebase_auth_manager._initialized:
        print(f"✅ Firebase is initialized!")
        print(f"App name: {firebase_auth_manager._app.name if firebase_auth_manager._app else 'N/A'}")
        print(f"Project ID: {firebase_auth_manager._app.project_id if firebase_auth_manager._app else 'N/A'}")
        print(f"Firestore client: {'✅ Available' if firebase_auth_manager._firestore_db else '❌ Not available'}")
    else:
        print("❌ Firebase is NOT initialized!")
        if firebase_auth_manager._initialization_history:
            print("\nInitialization history:")
            for entry in firebase_auth_manager._initialization_history:
                print(f"  - {entry}")

print("\n" + "=" * 60)
print("Step 4: Check user creation flow")
print("=" * 60)
# Simulate what happens when a user logs in with Firebase token
fake_firebase_token = {
    'uid': 'test-uid-123',
    'email': 'test@example.com',
    'name': 'Test User'
}

try:
    user = firebase_auth_manager.get_or_create_user(fake_firebase_token)
    if user:
        print(f"✅ User creation/retrieval works!")
        print(f"   User type: {type(user)}")
        if isinstance(user, dict):
            print(f"   User email: {user.get('email')}")
            print(f"   User ID: {user.get('id')}")
        else:
            print(f"   User email: {user.email}")
            print(f"   User ID: {user.id}")
    else:
        print("❌ User creation/retrieval returned None")
except Exception as e:
    print(f"❌ Error in user creation: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
