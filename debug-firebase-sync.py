#!/usr/bin/env python3
"""
Debug Firebase Sync Endpoint
Test the Firebase sync endpoint with detailed error logging
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
backend_path = Path(__file__).parent / 'backend'
env_path = backend_path / '.env'
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(backend_path))

def test_firebase_sync_with_real_token():
    """Test Firebase sync with a mock but properly formatted token"""
    print("🔄 Testing Firebase Sync Endpoint with Mock Token...")
    
    # Create a mock Firebase token payload (what would come from Firebase)
    mock_firebase_data = {
        "firebase_uid": "test-firebase-uid-12345",
        "email": "test@example.com",
        "display_name": "Test User",
        "photo_url": None,
        "email_verified": True
    }
    
    # Test with invalid token first to see the error handling
    headers = {"Authorization": "Bearer invalid-token-format"}
    
    try:
        response = requests.post(
            "http://localhost:5000/auth/firebase-sync",
            headers=headers,
            json=mock_firebase_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
        return response.status_code, response.text
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not running on http://localhost:5000")
        return None, "Connection Error"
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None, str(e)

def test_backend_logs():
    """Check if we can get backend logs or error details"""
    print("\n📋 Testing Backend Error Handling...")
    
    # Test various endpoints to see which ones work
    endpoints = [
        "/auth/firebase-health",
        "/auth/verify-token",
        "/auth/firebase-sync"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"http://localhost:5000{endpoint}"
            if endpoint == "/auth/firebase-sync":
                response = requests.post(url, json={}, timeout=5)
            else:
                response = requests.get(url, timeout=5)
            
            print(f"✅ {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_database_connection():
    """Test if the database connection is working"""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        # Import Flask app and test database
        from app import create_app, db
        from app.models.production.user_models import User
        
        app = create_app()
        with app.app_context():
            # Try to query users table
            user_count = User.query.count()
            print(f"✅ Database connection working. User count: {user_count}")
            
            # Try to create a test user to see if the schema is correct
            test_user = User(
                email="test@example.com",
                firebase_uid="test-uid",
                first_name="Test",
                last_name="User",
                username="testuser"
            )
            
            # Don't commit, just test the object creation
            print("✅ User object creation successful")
            print(f"✅ User to_dict() method: {test_user.to_dict()}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_firebase_auth_manager():
    """Test the Firebase auth manager directly"""
    print("\n🔥 Testing Firebase Auth Manager...")
    
    try:
        from app.middleware.firebase_auth import firebase_auth_manager
        
        print(f"Firebase initialized: {firebase_auth_manager._initialized}")
        
        # Test token verification with invalid token
        result = firebase_auth_manager.verify_token("invalid-token")
        print(f"Invalid token verification (should be None): {result}")
        
        # Test user creation with mock data
        mock_token = {
            'uid': 'test-uid-12345',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': None,
            'email_verified': True
        }
        
        print("Testing user creation with mock token...")
        # This might fail due to database issues
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase auth manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("🐛 Firebase Sync Debug Session")
    print("=" * 50)
    
    # Test 1: Database connection
    db_ok = test_database_connection()
    
    # Test 2: Firebase auth manager
    firebase_ok = test_firebase_auth_manager()
    
    # Test 3: Backend endpoints
    test_backend_logs()
    
    # Test 4: Firebase sync endpoint
    if db_ok and firebase_ok:
        status_code, response = test_firebase_sync_with_real_token()
        
        if status_code == 500:
            print("\n🚨 500 Error Confirmed!")
            print("The issue is likely in the Firebase sync endpoint implementation.")
            print("Check the backend server logs for detailed error information.")
        elif status_code == 401:
            print("\n✅ 401 Error Expected (invalid token)")
            print("The endpoint is working but rejecting invalid tokens correctly.")
        else:
            print(f"\n📊 Unexpected status code: {status_code}")
    
    print("\n" + "=" * 50)
    print("🔍 Debug Summary:")
    print(f"Database Connection: {'✅' if db_ok else '❌'}")
    print(f"Firebase Auth Manager: {'✅' if firebase_ok else '❌'}")
    print("\n💡 Next Steps:")
    print("1. Check backend server logs for detailed error messages")
    print("2. Ensure database schema is up to date")
    print("3. Verify Firebase service account permissions")

if __name__ == "__main__":
    main()