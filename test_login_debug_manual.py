#!/usr/bin/env python3
"""
Manual debug script to test login endpoint and identify 500 error source
"""
import requests
import json
import sys

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get("http://127.0.0.1:5001/api/health", timeout=5)
        print(f"✅ Server health check: {response.status_code}")
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server on port 5001")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_login_endpoint():
    """Test the login endpoint with detailed error reporting"""
    
    # Test URL (port 5001 based on the terminal selection)
    login_url = "http://127.0.0.1:5001/api/auth/login"
    
    # Test with sample data
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    print(f"🔍 Testing login endpoint: {login_url}")
    print(f"📝 Login data: {json.dumps(login_data, indent=2)}")
    
    try:
        # Make the request with proper headers
        response = requests.post(
            login_url, 
            json=login_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        print(f"\n📊 Response Details:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        # Try to parse response
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                response_data = response.json()
                print(f"   JSON Response: {json.dumps(response_data, indent=2)}")
            else:
                print(f"   Raw Response: {response.text[:500]}...")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Parse Error: {e}")
            print(f"   Raw Response: {response.text[:500]}...")
            
        # Check for specific 500 error patterns
        if response.status_code == 500:
            print(f"\n🚨 500 ERROR DETECTED!")
            print(f"   This indicates a backend crash during login processing")
            
            # Common causes analysis
            print(f"\n🔍 Possible causes:")
            print(f"   1. Database connection issue")
            print(f"   2. Missing environment variables (JWT_SECRET, DATABASE_URL)")
            print(f"   3. User model/table structure mismatch")
            print(f"   4. Password hashing/verification error")
            print(f"   5. Flask app configuration issue")
            
        return response
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is Flask running on port 5001?")
        return None
    except requests.exceptions.Timeout:
        print("❌ Request timeout. Server may be overloaded or stuck.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_database_endpoint():
    """Test a simple database query endpoint"""
    try:
        # Try a simple endpoint that doesn't require auth
        response = requests.get("http://127.0.0.1:5001/api/health", timeout=5)
        print(f"📊 Database test via health endpoint: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_with_existing_user():
    """Test with a user that might exist in the database"""
    
    # Try some common test emails that might be in the database
    test_users = [
        {"email": "admin@example.com", "password": "admin123"},
        {"email": "test@test.com", "password": "testpassword123"},
        {"email": "user@example.com", "password": "password123"},
    ]
    
    print(f"\n🔄 Testing with potentially existing users...")
    
    for user_data in test_users:
        print(f"\n📝 Trying user: {user_data['email']}")
        
        try:
            response = requests.post(
                "http://127.0.0.1:5001/api/auth/login",
                json=user_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Login successful!")
                try:
                    data = response.json()
                    if 'access_token' in data:
                        print(f"   🎫 Token received: {data['access_token'][:20]}...")
                except:
                    pass
                return True
            elif response.status_code == 401:
                print(f"   🔐 Invalid credentials (expected for test data)")
            elif response.status_code == 500:
                print(f"   🚨 500 error - backend crashed!")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}...")
                return False
            else:
                print(f"   ⚠️ Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    return False

def main():
    """Main debug function"""
    print("🔍 LOGIN ENDPOINT DEBUG SCRIPT")
    print("=" * 50)
    
    # Step 1: Check if server is running
    print("\n1️⃣ Testing server connectivity...")
    if not test_server_health():
        print("❌ Server is not responding. Please start the Flask backend first.")
        sys.exit(1)
    
    # Step 2: Test database connectivity
    print("\n2️⃣ Testing database connectivity...")
    if not test_database_endpoint():
        print("⚠️ Database connectivity issues detected.")
    
    # Step 3: Test login endpoint with sample data
    print("\n3️⃣ Testing login endpoint with sample data...")
    response = test_login_endpoint()
    
    # Step 4: Test with potentially existing users
    print("\n4️⃣ Testing with potentially existing users...")
    success = test_with_existing_user()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 DEBUG SUMMARY:")
    
    if response and response.status_code == 500:
        print("❌ CONFIRMED: Login endpoint returns 500 error")
        print("💡 ACTION NEEDED: Check backend console logs for stack trace")
        print("💡 LIKELY CAUSES:")
        print("   - Database connection failure")
        print("   - Missing environment variables")
        print("   - User model/table structure issues")
        print("   - Password hashing library problems")
    elif success:
        print("✅ Login endpoint working with existing user")
        print("💡 Issue might be with specific user data or registration")
    else:
        print("⚠️ Mixed results - need to check backend logs")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Check backend terminal for error messages")
    print("2. Verify DATABASE_URL environment variable")
    print("3. Check if users table exists and has proper structure")
    print("4. Verify JWT_SECRET_KEY is set")

if __name__ == '__main__':
    main()
