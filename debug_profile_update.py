#!/usr/bin/env python3
"""
Debug Profile Update Issue
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:5000"

def debug_profile_update():
    session = requests.Session()
    
    # Step 1: Register
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"debuguser_{timestamp}@example.com"
    # Use environment variable or generate a test credential
    test_pwd = os.getenv("DEBUG_TEST_PASSWORD", "test123")
    
    print("🔧 DEBUG: Testing profile update endpoint")
    print(f"📧 Email: {test_email}")
    
    # Register
    register_data = {
        "email": test_email,
        "password": test_pwd,
        "username": f"debuguser_{timestamp}",
        "organizationName": "Debug Organization"
    }
    
    register_response = session.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"📝 Registration status: {register_response.status_code}")
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return
    
    # Login
    login_data = {"email": test_email, "password": test_pwd}
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"🔑 Login status: {login_response.status_code}")
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    # Get token
    login_data = login_response.json()
    access_token = login_data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    print(f"✅ Token acquired")
    
    # Test profile update with minimal data
    print("\n🧪 Testing profile update...")
    update_data = {
        "first_name": "Debug",
        "last_name": "User",
        "username": f"debug_{timestamp}",  # Shorter username
        "timezone": "UTC",
        "language": "en",
        "theme": "light",
        "email_notifications": True,
        "push_notifications": False
    }
    
    print(f"📤 Sending update data: {json.dumps(update_data, indent=2)}")
    
    try:
        update_response = session.put(f"{BASE_URL}/api/users/profile", json=update_data)
        print(f"📥 Response status: {update_response.status_code}")
        print(f"📥 Response headers: {dict(update_response.headers)}")
        print(f"📥 Response body: {update_response.text}")
        
        if update_response.status_code == 200:
            print("✅ Profile update successful!")
        else:
            print(f"❌ Profile update failed")
            
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")

if __name__ == "__main__":
    debug_profile_update()
