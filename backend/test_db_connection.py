#!/usr/bin/env python3
"""
Simple database connection test
"""
import requests
import json

def test_database_connection():
    """Test if we can query the database"""
    
    # Test URL - let's try to register a user first to see if DB works
    base_url = "http://127.0.0.1:5000"
    register_url = f"{base_url}/api/auth/register"
    
    # Sample registration data
    register_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    print(f"Testing registration endpoint: {register_url}")
    print(f"Registration data: {json.dumps(register_data, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(
            register_url, 
            json=register_data,
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

if __name__ == "__main__":
    print("=== Database Connection Test ===\n")
    test_database_connection()
