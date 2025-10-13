#!/usr/bin/env python3
"""
Test specific endpoints to identify the exact issue
"""
import requests
import json

def test_endpoints():
    """Test specific endpoints to identify the issue"""
    
    base_url = "http://127.0.0.1:5001"
    
    endpoints_to_test = [
        {"url": f"{base_url}/", "name": "Root"},
        {"url": f"{base_url}/health", "name": "Health Check"},
        {"url": f"{base_url}/api", "name": "API Root"},
        {"url": f"{base_url}/api/health", "name": "API Health"},
        {"url": f"{base_url}/api/auth", "name": "Auth Root"},
        {"url": f"{base_url}/api/auth/login", "name": "Login Endpoint", "method": "POST", "data": {"email": "test@test.com", "password": "test"}},
    ]
    
    print("🔍 ENDPOINT TESTING")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = endpoint["url"]
        name = endpoint["name"]
        method = endpoint.get("method", "GET")
        data = endpoint.get("data")
        
        print(f"\n📍 Testing {name}: {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(
                    url, 
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
            
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS")
            elif response.status_code == 404:
                print(f"   ❌ NOT FOUND - Endpoint not registered")
            elif response.status_code == 500:
                print(f"   🚨 SERVER ERROR - Backend crashed")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}...")
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                
            # Show response preview
            if len(response.text) < 200:
                print(f"   Response: {response.text}")
            else:
                print(f"   Response: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION FAILED - Server not running")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def test_login_with_verbose_error():
    """Test login with detailed error handling"""
    print(f"\n🔍 DETAILED LOGIN TEST")
    print("=" * 30)
    
    login_url = "http://127.0.0.1:5001/api/auth/login"
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    try:
        response = requests.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 500:
            print(f"🚨 500 ERROR DETAILS:")
            try:
                error_data = response.json()
                print(f"JSON Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw Error Response:")
                print(response.text)
        elif response.status_code == 404:
            print(f"❌ 404 - Login endpoint not found!")
            print(f"This means the auth blueprint is not properly registered.")
        else:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            except:
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == '__main__':
    test_endpoints()
    test_login_with_verbose_error()
