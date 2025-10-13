#!/usr/bin/env python3
"""
Firebase Test Script
Tests Firebase Admin SDK initialization and token verification
"""

import os
import sys
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_firebase_setup():
    """Test Firebase setup"""
    print("🔥 Testing Firebase Admin SDK Setup...")
    
    try:
        import firebase_admin
        from firebase_admin import auth, credentials
        
        print("✅ Firebase Admin SDK imported successfully")
        
        # Load environment variables
        from app.core.env_loader import load_environment
        load_environment()
        
        # Check service account file
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if service_account_path and os.path.exists(service_account_path):
            print(f"✅ Service account file found: {service_account_path}")
            
            # Load and validate service account
            with open(service_account_path, 'r') as f:
                service_account = json.load(f)
            
            print(f"📊 Project ID: {service_account.get('project_id')}")
            print(f"📧 Client Email: {service_account.get('client_email')}")
        else:
            print(f"❌ Service account file not found: {service_account_path}")
            return False
        
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin SDK initialized successfully!")
            except Exception as e:
                print(f"❌ Firebase initialization failed: {e}")
                return False
        else:
            print("✅ Firebase Admin SDK already initialized")
        
        # Test token verification (with dummy token - will fail but should not crash)
        try:
            # This will fail but tests that the auth module works
            auth.verify_id_token("dummy-token")
        except Exception as e:
            if "Invalid ID token" in str(e) or "Token used too early" in str(e) or "Incorrect number of segments" in str(e):
                print("✅ Token verification module working (expected failure with dummy token)")
            else:
                print(f"⚠️ Unexpected error in token verification: {e}")
        
        print("🎉 Firebase setup test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Firebase Admin SDK import failed: {e}")
        print("💡 Run: pip install firebase-admin")
        return False
    except Exception as e:
        print(f"❌ Firebase test failed: {e}")
        return False

def test_environment_variables():
    """Test Firebase environment variables"""
    print("\n🔧 Testing Firebase Environment Variables...")
    
    firebase_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_SERVICE_ACCOUNT_PATH',
        'FIREBASE_CLIENT_EMAIL',
        'FIREBASE_CLIENT_ID'
    ]
    
    all_present = True
    for var in firebase_vars:
        value = os.getenv(var)
        if value:
            if 'PRIVATE_KEY' in var:
                print(f"✅ {var}: [PRESENT - HIDDEN]")
            elif 'SERVICE_ACCOUNT_PATH' in var:
                exists = os.path.exists(value) if value else False
                print(f"✅ {var}: {value} {'(exists)' if exists else '(NOT FOUND)'}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("🚀 Firebase Integration Test")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test Firebase setup
    firebase_ok = test_firebase_setup()
    
    print("\n" + "=" * 50)
    if env_ok and firebase_ok:
        print("🎉 All Firebase tests passed!")
        print("\n💡 You can now:")
        print("   1. Start your backend server")
        print("   2. Test Firebase auth endpoints")
        print("   3. Use Firebase authentication in your frontend")
    else:
        print("❌ Some Firebase tests failed")
        print("🔧 Check your configuration and try again")
    
    sys.exit(0 if (env_ok and firebase_ok) else 1)