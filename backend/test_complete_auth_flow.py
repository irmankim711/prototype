#!/usr/bin/env python3
"""
Complete JWT Authentication Flow Test
Tests login, token usage, and dashboard access.
"""

import requests
import json

def test_complete_auth_flow():
    """Test complete authentication flow"""
    print("=== COMPLETE AUTHENTICATION FLOW TEST ===\n")
    
    base_url = "http://localhost:5000"
    
    # Step 1: Test Registration (if needed)
    print("📝 Step 1: Test Registration")
    register_data = {
        "email": "testjwt@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data, timeout=10)
        if response.status_code == 201:
            print("  ✅ Registration successful")
        elif response.status_code == 409:
            print("  ℹ️  User already exists")
        else:
            print(f"  ❌ Registration failed: {response.status_code}")
            try:
                print(f"    Response: {response.json()}")
            except:
                print(f"    Response: {response.text}")
    except Exception as e:
        print(f"  ❌ Registration error: {e}")
    
    # Step 2: Test Login
    print(f"\n🔐 Step 2: Test Login")
    login_data = {
        "email": "testjwt@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            access_token = login_result.get("access_token")
            print("  ✅ Login successful")
            print(f"  User ID: {login_result.get('user', {}).get('id')}")
            print(f"  Token preview: {access_token[:50]}..." if access_token else "No token")
            
            # Step 3: Test Protected Route with Token
            print(f"\n🛡️  Step 3: Test Protected Routes with Token")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            protected_endpoints = [
                "/api/auth/me",
                "/api/dashboard/stats",
                "/api/dashboard/summary",
                "/api/dashboard/charts"
            ]
            
            for endpoint in protected_endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
                    status_color = "✅" if response.status_code == 200 else "❌" if response.status_code >= 400 else "⚠️"
                    print(f"    {endpoint:25} {status_color} {response.status_code}")
                    
                    # Show error details for debugging
                    if response.status_code >= 400:
                        try:
                            error_data = response.json()
                            if 'msg' in error_data:
                                print(f"      Error: {error_data['msg']}")
                            elif 'error' in error_data:
                                print(f"      Error: {error_data['error']}")
                        except:
                            print(f"      Response: {response.text[:100]}")
                            
                except Exception as e:
                    print(f"    {endpoint:25} ❌ ERROR: {str(e)}")
            
            # Step 4: Test Token Refresh
            print(f"\n🔄 Step 4: Test Token Refresh")
            try:
                # Try to get cookies from login response
                cookies = response.cookies
                
                refresh_response = requests.post(
                    f"{base_url}/api/auth/refresh", 
                    cookies=cookies,
                    timeout=10
                )
                
                print(f"  Refresh status: {refresh_response.status_code}")
                if refresh_response.status_code == 200:
                    refresh_result = refresh_response.json()
                    new_token = refresh_result.get("access_token")
                    print("  ✅ Token refresh successful")
                    print(f"  New token preview: {new_token[:50]}..." if new_token else "No new token")
                else:
                    try:
                        error_data = refresh_response.json()
                        print(f"  ❌ Refresh failed: {error_data.get('msg', 'Unknown error')}")
                    except:
                        print(f"  ❌ Refresh failed: {refresh_response.text}")
                        
            except Exception as e:
                print(f"  ❌ Refresh error: {e}")
                
        else:
            print(f"  ❌ Login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('msg', 'Unknown error')}")
            except:
                print(f"  Response: {response.text}")
                
    except Exception as e:
        print(f"  ❌ Login error: {e}")

def test_jwt_error_scenarios():
    """Test various JWT error scenarios to ensure proper error handling"""
    print(f"\n=== JWT ERROR SCENARIO TESTS ===\n")
    
    base_url = "http://localhost:5000"
    
    error_tests = [
        ("No Token", "/api/auth/me", {}, "Should return 401"),
        ("Invalid Token", "/api/auth/me", {"Authorization": "Bearer invalid.token.here"}, "Should return 422"),
        ("Malformed Token", "/api/auth/me", {"Authorization": "Bearer malformed"}, "Should return 422"),
        ("Empty Auth Header", "/api/auth/me", {"Authorization": ""}, "Should return 401"),
    ]
    
    for test_name, endpoint, headers, expected in error_tests:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
            status_color = "✅" if response.status_code in [401, 422] else "❌"
            print(f"  {test_name:20} {status_color} {response.status_code} - {expected}")
            
            # Show error message
            try:
                error_data = response.json()
                print(f"    Message: {error_data.get('msg', error_data.get('message', 'No message'))}")
            except:
                pass
                
        except Exception as e:
            print(f"  {test_name:20} ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_complete_auth_flow()
    test_jwt_error_scenarios()
