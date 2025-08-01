#!/usr/bin/env python3
"""
Test 404 Error Fix - Frontend API Configuration
"""

import requests
import json

def test_endpoints():
    """Test the endpoints that frontend should be calling"""
    print("🔍 Testing Frontend API Endpoint Configuration Fix...")
    
    base_url = "http://localhost:5000"
    
    endpoints_to_test = [
        "/api/forms/public",
        "/api/auth/login",
        "/health"
    ]
    
    print(f"Backend base URL: {base_url}")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        full_url = f"{base_url}{endpoint}"
        print(f"\n🌐 Testing: {full_url}")
        
        try:
            if endpoint == "/api/auth/login":
                # POST request for login
                response = requests.post(full_url, json={
                    "email": "test@test.com", 
                    "password": "test123"
                })
            else:
                # GET request for others
                response = requests.get(full_url)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS: Endpoint working correctly")
                if endpoint == "/api/forms/public":
                    data = response.json()
                    if isinstance(data, dict) and 'forms' in data:
                        print(f"  📊 Found {len(data['forms'])} public forms")
                    else:
                        print(f"  📊 Response: {type(data)}")
            elif response.status_code == 404:
                print(f"  ❌ 404 NOT FOUND: This would cause the frontend error")
            else:
                print(f"  ⚠️  Status {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ❌ CONNECTION ERROR: Backend not accessible at {base_url}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("📋 DIAGNOSIS:")
    print("If all endpoints return 200, the frontend should work correctly.")
    print("If any return 404, that's the source of your frontend error.")
    print("\n💡 FRONTEND CONFIGURATION:")
    print("Frontend should use: http://localhost:5000/api")
    print("NOT: http://localhost:5174/api (which would give 404)")

if __name__ == "__main__":
    test_endpoints()
