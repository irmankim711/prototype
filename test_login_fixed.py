#!/usr/bin/env python3
"""
Test login endpoint after fixing the user table
"""
import requests
import json

def test_login_fixed():
    """Test login with the created test user"""
    
    login_url = "http://127.0.0.1:5001/api/auth/login"
    
    # Test with the created test user
    test_credentials = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    print("🔍 TESTING LOGIN AFTER FIX")
    print("=" * 40)
    print(f"URL: {login_url}")
    print(f"Credentials: {test_credentials['email']} / {test_credentials['password']}")
    
    try:
        response = requests.post(
            login_url,
            json=test_credentials,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\n📊 RESULTS:")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            print(f"🎉 SUCCESS! Login works!")
            try:
                data = response.json()
                print(f"✅ Received access token: {data.get('access_token', 'N/A')[:30]}...")
                print(f"✅ User data: {data.get('user', {})}")
                return True
            except Exception as e:
                print(f"⚠️ Could not parse JSON response: {e}")
                print(f"Raw response: {response.text}")
                return False
                
        elif response.status_code == 401:
            print(f"🔐 AUTHENTICATION FAILED")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw error: {response.text}")
            return False
            
        elif response.status_code == 500:
            print(f"🚨 STILL GETTING 500 ERROR")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error: {response.text}")
            return False
            
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server. Is Flask running on port 5001?")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_other_endpoints():
    """Test other endpoints to make sure they work"""
    
    endpoints = [
        "http://127.0.0.1:5001/health",
        "http://127.0.0.1:5001/api/auth/register"
    ]
    
    print(f"\n🔍 TESTING OTHER ENDPOINTS:")
    print("-" * 30)
    
    for url in endpoints:
        try:
            if "register" in url:
                # Test POST for register
                test_data = {
                    "email": "newuser@test.com",
                    "password": "newpassword123",
                    "first_name": "New",
                    "last_name": "User"
                }
                response = requests.post(url, json=test_data, timeout=5)
            else:
                response = requests.get(url, timeout=5)
                
            print(f"{url}: {response.status_code}")
            
        except Exception as e:
            print(f"{url}: ERROR - {e}")

if __name__ == '__main__':
    success = test_login_fixed()
    test_other_endpoints()
    
    if success:
        print(f"\n🎉 LOGIN ENDPOINT IS WORKING!")
        print(f"The 500 error has been fixed.")
        print(f"You can now use the frontend login form.")
    else:
        print(f"\n❌ Login still has issues.")
        print(f"Check the error details above.")
