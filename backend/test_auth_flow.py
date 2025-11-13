#!/usr/bin/env python3
"""
Test Authentication Flow
Verifies JWT authentication and identifies 422 error causes
"""

import requests
import json
from datetime import datetime

def test_authentication_flow():
    """Test the complete authentication flow"""
    base_url = "http://localhost:5000"
    
    print("🔐 Testing Authentication Flow...")
    print("=" * 50)
    
    # Test 1: Health check (no auth required)
    print("\n🔍 Test 1: Health Check (No Auth)")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"  Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
    
    # Test 2: CORS test endpoint (no auth required)
    print("\n🔍 Test 2: CORS Test Endpoint (No Auth)")
    try:
        response = requests.get(f"{base_url}/api/v1/nextgen/cors-test")
        print(f"  Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
    
    # Test 3: NextGen endpoints with auth (should get 401 without token)
    print("\n🔍 Test 3: NextGen Endpoints (No Auth - Should Get 401)")
    endpoints = [
        "/api/v1/nextgen/data-sources",
        "/api/v1/nextgen/templates"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"  {endpoint}: {response.status_code}")
            if response.status_code == 401:
                print(f"    ✅ Expected 401 (no token)")
            elif response.status_code == 422:
                print(f"    ⚠️ Got 422 (token validation issue)")
                print(f"    Response: {response.text}")
            else:
                print(f"    ❌ Unexpected status: {response.text}")
        except Exception as e:
            print(f"  ❌ {endpoint}: Failed - {e}")
    
    # Test 4: Check if there are any public auth endpoints
    print("\n🔍 Test 4: Looking for Auth Endpoints")
    try:
        response = requests.get(f"{base_url}/api/auth")
        print(f"  /api/auth: {response.status_code}")
        if response.ok:
            print(f"    Response: {response.text}")
        else:
            print(f"    Error: {response.text}")
    except Exception as e:
        print(f"  ❌ /api/auth: Failed - {e}")
    
    print("\n" + "=" * 50)
    print("✅ Authentication Flow Test Complete")
    print("\n📋 Analysis:")
    print("  - 200 responses: Endpoints working without auth")
    print("  - 401 responses: Endpoints require auth (expected)")
    print("  - 422 responses: Auth working but validation failing")
    print("  - 500 responses: Server errors (unexpected)")

if __name__ == "__main__":
    test_authentication_flow()
