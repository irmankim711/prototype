#!/usr/bin/env python3
"""
Test script to simulate frontend API calls and identify 500 errors
"""

import requests
import json

def test_api_endpoint(url, method='GET', data=None, headers=None):
    """Test an API endpoint and return detailed results"""
    try:
        if method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        
        print(f"{method} {url}")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code >= 400:
            print(f"Error Response: {response.text}")
            return False
        else:
            try:
                json_data = response.json()
                print(f"Success: {len(str(json_data))} chars")
                return True
            except:
                print(f"Success: {len(response.text)} chars (not JSON)")
                return True
                
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    base_url = "http://127.0.0.1:5000"
    
    print("Testing API endpoints that frontend might call...")
    print("=" * 60)
    
    # Test endpoints commonly used by frontend
    endpoints = [
        ("/health", "GET"),
        ("/api/forms/public", "GET"),
        ("/api/auth/login", "POST", {"email": "test@test.com", "password": "test123"}),
    ]
    
    token = None
    
    for endpoint_info in endpoints:
        if len(endpoint_info) == 2:
            endpoint, method = endpoint_info
            data = None
        else:
            endpoint, method, data = endpoint_info
            
        print(f"\n{'-'*40}")
        
        # For login, get token for subsequent requests
        if endpoint == "/api/auth/login" and method == "POST":
            try:
                response = requests.post(f"{base_url}{endpoint}", json=data)
                if response.status_code == 200:
                    token = response.json().get('access_token')
                    print(f"POST {endpoint}")
                    print(f"Status: {response.status_code}")
                    print("Token obtained for subsequent requests")
                else:
                    print(f"Login failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Login error: {e}")
            continue
        
        # Test with auth header if we have a token
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        test_api_endpoint(f"{base_url}{endpoint}", method, data, headers)
    
    # Test protected endpoints with token
    if token:
        print(f"\n{'-'*40}")
        print("Testing protected endpoints with token...")
        
        protected_endpoints = [
            "/api/users/profile",
            "/api/forms",
        ]
        
        for endpoint in protected_endpoints:
            print(f"\n{'-'*20}")
            headers = {'Authorization': f'Bearer {token}'}
            test_api_endpoint(f"{base_url}{endpoint}", "GET", headers=headers)

if __name__ == "__main__":
    main()
