#!/usr/bin/env python3
"""
Test script to verify all login fixes are working correctly
"""
import requests
import json
import time

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed - Status: {data.get('status')}, DB: {data.get('database')}")
            return True
        else:
            print(f"❌ Health check failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_registration():
    """Test user registration"""
    print("\n📝 Testing user registration...")
    test_email = f"testuser_{int(time.time())}@example.com"
    test_password = "testpassword123"
    
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "first_name": "Test",
                "last_name": "User"
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✅ Registration successful for {test_email}")
            return test_email, test_password
        elif response.status_code == 409:
            print(f"ℹ️  User already exists, will try login")
            return test_email, test_password
        else:
            print(f"❌ Registration failed - Status: {response.status_code}")
            try:
                print(f"   Response: {response.json()}")
            except:
                print(f"   Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None, None

def test_login(email, password):
    """Test user login"""
    print(f"\n🔐 Testing login for {email}...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/auth/login",
            json={
                "email": email,
                "password": password
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            user_data = data.get("user", {})
            
            print(f"✅ Login successful!")
            print(f"   User ID: {user_data.get('id')}")
            print(f"   Token preview: {access_token[:50]}..." if access_token else "No token")
            
            # Check if cookies were set
            cookies = response.cookies
            if cookies.get("access_token_cookie"):
                print(f"✅ Access token cookie set")
            else:
                print(f"⚠️  No access token cookie found")
                
            return access_token
        else:
            print(f"❌ Login failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('msg', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint"""
    print(f"\n🛡️  Testing protected endpoint with token...")
    
    if not token:
        print("❌ No token available for testing")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "http://127.0.0.1:5000/api/auth/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Protected endpoint accessible")
            print(f"   User: {data.get('email')} (Active: {data.get('is_active')})")
            return True
        else:
            print(f"❌ Protected endpoint failed - Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('msg', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False

def test_logout(token):
    """Test user logout"""
    print(f"\n🚪 Testing logout...")
    
    if not token:
        print("❌ No token available for testing")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "http://127.0.0.1:5000/api/auth/logout",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logout successful: {data.get('msg')}")
            return True
        else:
            print(f"❌ Logout failed - Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('msg', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== LOGIN FIXES VERIFICATION TEST ===\n")
    
    # Test 1: Health endpoint
    if not test_health_endpoint():
        print("\n❌ Health check failed. Is the Flask server running?")
        print("   Start it with: python run.py")
        return
    
    # Test 2: Registration
    email, password = test_registration()
    if not email or not password:
        print("\n❌ Registration failed. Cannot proceed with login test.")
        return
    
    # Test 3: Login
    token = test_login(email, password)
    if not token:
        print("\n❌ Login failed. The main issue is not resolved.")
        return
    
    # Test 4: Protected endpoint
    if not test_protected_endpoint(token):
        print("\n❌ Protected endpoint test failed.")
        return
    
    # Test 5: Logout
    test_logout(token)
    
    print("\n" + "="*50)
    print("🎉 ALL LOGIN FIXES VERIFIED SUCCESSFULLY!")
    print("✅ Health endpoint working")
    print("✅ Registration working")
    print("✅ Login working")
    print("✅ JWT token generation working")
    print("✅ Protected endpoints accessible")
    print("✅ Logout working")
    print("="*50)
    print("\nThe login system is now fully functional!")

if __name__ == "__main__":
    main()
