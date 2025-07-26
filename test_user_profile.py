#!/usr/bin/env python3
"""
Test script to verify user profile functionality works correctly.
Run this script to test the enhanced user profile features.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the backend directory to the path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# API Base URL
BASE_URL = "http://localhost:5000"

def test_user_profile():
    """Test user profile functionality"""
    print("🧪 Testing Enhanced User Profile Functionality")
    print("=" * 50)
    
    # Test data
    test_email = "testuser@example.com"
    test_password = "testpassword123"
    
    session = requests.Session()
    
    try:
        # 1. Test registration (if needed)
        print("\n1. Testing user registration...")
        register_data = {
            "email": test_email,
            "password": test_password
        }
        
        register_response = session.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if register_response.status_code == 201:
            print("✅ User registered successfully")
        elif register_response.status_code == 409:
            print("ℹ️  User already exists, proceeding to login")
        else:
            print(f"❌ Registration failed: {register_response.text}")
            return False
        
        # 2. Test login
        print("\n2. Testing user login...")
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        login_result = login_response.json()
        token = login_result["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ User logged in successfully")
        
        # 3. Test get profile
        print("\n3. Testing get profile...")
        profile_response = session.get(f"{BASE_URL}/api/users/profile")
        if profile_response.status_code != 200:
            print(f"❌ Get profile failed: {profile_response.text}")
            return False
        
        profile_data = profile_response.json()
        print("✅ Profile retrieved successfully")
        print(f"   User ID: {profile_data.get('id')}")
        print(f"   Email: {profile_data.get('email')}")
        print(f"   Role: {profile_data.get('role')}")
        
        # 4. Test update profile
        print("\n4. Testing update profile...")
        update_data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": f"johndoe_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "phone": "+1-555-123-4567",
            "company": "StratoSys Corp",
            "job_title": "Software Engineer",
            "bio": "Passionate developer working on innovative solutions.",
            "timezone": "America/New_York",
            "language": "en",
            "theme": "light",
            "email_notifications": True,
            "push_notifications": False
        }
        
        update_response = session.put(f"{BASE_URL}/api/users/profile", json=update_data)
        if update_response.status_code != 200:
            print(f"❌ Update profile failed: {update_response.text}")
            return False
        
        update_result = update_response.json()
        print("✅ Profile updated successfully")
        print(f"   Message: {update_result.get('message')}")
        
        # Verify the updated data
        updated_user = update_result.get('user', {})
        print(f"   Updated Name: {updated_user.get('first_name')} {updated_user.get('last_name')}")
        print(f"   Updated Company: {updated_user.get('company')}")
        print(f"   Updated Job Title: {updated_user.get('job_title')}")
        
        # 5. Test get updated profile
        print("\n5. Testing get updated profile...")
        updated_profile_response = session.get(f"{BASE_URL}/api/users/profile")
        if updated_profile_response.status_code != 200:
            print(f"❌ Get updated profile failed: {updated_profile_response.text}")
            return False
        
        updated_profile_data = updated_profile_response.json()
        print("✅ Updated profile retrieved successfully")
        print(f"   Full Name: {updated_profile_data.get('full_name')}")
        print(f"   Username: {updated_profile_data.get('username')}")
        print(f"   Phone: {updated_profile_data.get('phone')}")
        print(f"   Timezone: {updated_profile_data.get('timezone')}")
        print(f"   Email Notifications: {updated_profile_data.get('email_notifications')}")
        
        # 6. Test user settings
        print("\n6. Testing user settings...")
        settings_response = session.get(f"{BASE_URL}/api/users/settings")
        if settings_response.status_code != 200:
            print(f"❌ Get settings failed: {settings_response.text}")
            return False
        
        settings_data = settings_response.json()
        print("✅ Settings retrieved successfully")
        print(f"   Settings: {json.dumps(settings_data, indent=2)}")
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend server.")
        print("   Make sure the backend is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_user_profile()
    sys.exit(0 if success else 1)
