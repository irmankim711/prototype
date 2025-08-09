#!/usr/bin/env python3
"""
Debug script to test login endpoint and identify 500 error source
"""
import requests
import json

def test_login_endpoint():
    """Test the login endpoint with sample data"""
    
    # Test URL
    base_url = "http://127.0.0.1:5000"
    login_url = f"{base_url}/api/auth/login"
    
    # Sample login data
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    print(f"Testing login endpoint: {login_url}")
    print(f"Login data: {json.dumps(login_data, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(
            login_url, 
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
        return response
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is the Flask server running on port 5000?")
        return None
    except Exception as e:
        print(f"❌ Error making request: {e}")
        return None

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://127.0.0.1:5000/api/health", timeout=5)
        print(f"✅ Server is running - Health check status: {response.status_code}")
        return True
    except:
        try:
            # Try basic root endpoint
            response = requests.get("http://127.0.0.1:5000/", timeout=5)
            print(f"✅ Server is running - Root status: {response.status_code}")
            return True
        except:
            print("❌ Server appears to be down")
            return False

if __name__ == "__main__":
    print("=== Login Endpoint Debug Test ===\n")
    
    # Check server status first
    if check_server_status():
        # Test login endpoint
        test_login_endpoint()
    else:
        print("\nPlease start the Flask server first:")
        print("cd backend && python run.py")
