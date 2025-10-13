#!/usr/bin/env python3
"""
Debug script to test the Google Forms status endpoint
"""

import requests
import json

def test_google_forms_status():
    """Test the Google Forms status endpoint"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 Testing Google Forms status endpoint...")
    
    # Test without authentication (should get 401)
    print("\n1. Testing without authentication:")
    try:
        response = requests.get(f"{base_url}/api/google-forms/status")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test with fake token (should get 422)
    print("\n2. Testing with fake token:")
    try:
        headers = {"Authorization": "Bearer fake_token"}
        response = requests.get(f"{base_url}/api/google-forms/status", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test login endpoint to get a real token
    print("\n3. Testing login to get valid token:")
    try:
        login_data = {
            "email": "test@example.com",
            "password": "test123"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"   Login Response: {token_data}")
            
            if token_data.get('access_token'):
                print("\n4. Testing with valid token:")
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                response = requests.get(f"{base_url}/api/google-forms/status", headers=headers)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
        else:
            print(f"   Login failed: {response.json()}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_google_forms_status()
