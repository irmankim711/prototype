#!/usr/bin/env python3
"""
Test CORS Configuration
Verifies that CORS headers are properly set for NextGen endpoints
"""

import requests
import json
from urllib.parse import urljoin

def test_cors_configuration():
    """Test CORS configuration for NextGen endpoints"""
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        "/api/v1/nextgen/data-sources",
        "/api/v1/nextgen/data-sources/1/fields",
        "/api/v1/nextgen/templates",
        "/health"
    ]
    
    print("🧪 Testing CORS Configuration...")
    print("=" * 50)
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        
        # Test OPTIONS request (preflight)
        try:
            options_response = requests.options(
                urljoin(base_url, endpoint),
                headers={
                    'Origin': 'http://localhost:5173',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type,Authorization'
                }
            )
            
            print(f"  OPTIONS Status: {options_response.status_code}")
            print(f"  Access-Control-Allow-Origin: {options_response.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
            print(f"  Access-Control-Allow-Methods: {options_response.headers.get('Access-Control-Allow-Methods', 'NOT SET')}")
            print(f"  Access-Control-Allow-Headers: {options_response.headers.get('Access-Control-Allow-Headers', 'NOT SET')}")
            print(f"  Access-Control-Allow-Credentials: {options_response.headers.get('Access-Control-Allow-Credentials', 'NOT SET')}")
            print(f"  Access-Control-Max-Age: {options_response.headers.get('Access-Control-Max-Age', 'NOT SET')}")
            
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Connection failed - Is the server running on {base_url}?")
            continue
        except Exception as e:
            print(f"  ❌ OPTIONS request failed: {e}")
            continue
        
        # Test actual GET request
        try:
            get_response = requests.get(
                urljoin(base_url, endpoint),
                headers={'Origin': 'http://localhost:5173'}
            )
            
            print(f"  GET Status: {get_response.status_code}")
            print(f"  Access-Control-Allow-Origin: {get_response.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
            print(f"  Access-Control-Allow-Credentials: {get_response.headers.get('Access-Control-Allow-Credentials', 'NOT SET')}")
            
        except Exception as e:
            print(f"  ❌ GET request failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ CORS Configuration Test Complete")

if __name__ == "__main__":
    test_cors_configuration()
