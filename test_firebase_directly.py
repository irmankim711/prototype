#!/usr/bin/env python3
"""
Direct Firebase test to see what's actually happening
"""
import os
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_firebase_admin_direct():
    """Test Firebase Admin SDK directly"""
    print("🔥 Testing Firebase Admin SDK...")

    try:
        import firebase_admin
        from firebase_admin import credentials, auth

        # Check if already initialized
        if firebase_admin._apps:
            print("✅ Firebase already initialized")
            app = firebase_admin.get_app()
            print(f"App name: {app.name}")
            return True

        # Try to initialize with service account
        service_account_path = Path(__file__).parent / "backend" / "tokens" / "google" / "report-automation-57f6e-firebase-adminsdk-fbsvc-0af1714a80.json"

        print(f"🔍 Looking for service account at: {service_account_path}")
        print(f"File exists: {service_account_path.exists()}")

        if service_account_path.exists():
            try:
                # Read and validate the service account file
                with open(service_account_path, 'r') as f:
                    service_account_data = json.load(f)

                print(f"✅ Service account file loaded")
                print(f"Project ID: {service_account_data.get('project_id')}")
                print(f"Client Email: {service_account_data.get('client_email')}")
                print(f"Has Private Key: {'private_key' in service_account_data}")

                # Initialize Firebase
                cred = credentials.Certificate(str(service_account_path))
                app = firebase_admin.initialize_app(cred)

                print(f"✅ Firebase initialized successfully!")
                print(f"App name: {app.name}")
                print(f"Project ID: {app.project_id}")

                # Test token verification with a dummy token
                print("\n🔍 Testing token verification...")
                try:
                    # This should fail gracefully with an invalid token
                    decoded_token = auth.verify_id_token("invalid-token")
                    print("❌ This shouldn't happen - invalid token was accepted!")
                except Exception as e:
                    print(f"✅ Token validation correctly failed: {type(e).__name__}")
                    print(f"   Error: {str(e)[:100]}")

                return True

            except Exception as init_error:
                print(f"❌ Firebase initialization failed: {init_error}")
                print(f"Error type: {type(init_error)}")
                return False
        else:
            print("❌ Service account file not found")
            return False

    except ImportError as e:
        print(f"❌ Firebase Admin SDK not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_backend_firebase_manager():
    """Test the backend's Firebase manager"""
    print("\n🔧 Testing backend Firebase manager...")

    try:
        from app.middleware.firebase_auth import firebase_auth_manager

        print(f"Manager initialized: {firebase_auth_manager._initialized}")
        print(f"Initialization attempts: {firebase_auth_manager._initialization_attempts}")
        print(f"Initialization error: {firebase_auth_manager._initialization_error}")

        # Get initialization status
        status = firebase_auth_manager.get_initialization_status()
        print(f"Initialization status: {status}")

        # Try to verify a dummy token
        print("\n🔍 Testing token verification through manager...")
        result = firebase_auth_manager.verify_token("invalid-token")
        print(f"Token verification result: {result}")

        return True

    except Exception as e:
        print(f"❌ Backend Firebase manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment_variables():
    """Check Firebase environment variables"""
    print("\n🌍 Checking environment variables...")

    firebase_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'FIREBASE_PROJECT_ID',
        'FIREBASE_SERVICE_ACCOUNT_KEY'
    ]

    for var in firebase_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:50]}...")
        else:
            print(f"❌ {var}: NOT SET")

if __name__ == "__main__":
    print("🚀 Starting Firebase direct test...\n")

    check_environment_variables()

    direct_success = test_firebase_admin_direct()
    backend_success = test_backend_firebase_manager()

    print(f"\n📊 Results:")
    print(f"   Direct Firebase test: {'✅' if direct_success else '❌'}")
    print(f"   Backend manager test: {'✅' if backend_success else '❌'}")

    if direct_success and backend_success:
        print("\n✅ All tests passed - Firebase should be working!")
    else:
        print("\n❌ Some tests failed - this explains the login issue!")