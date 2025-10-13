#!/usr/bin/env python3
"""
Quick test script to check Form Builder API endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint and measure response time"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {url}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f}ms")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                if isinstance(json_data, dict):
                    print(f"Response Keys: {list(json_data.keys())}")
                    if 'forms' in json_data:
                        print(f"Number of forms: {len(json_data['forms'])}")
                elif isinstance(json_data, list):
                    print(f"Response Items: {len(json_data)}")
                else:
                    print(f"Response Type: {type(json_data)}")
            except:
                print(f"Response Text: {response.text[:200]}...")
        else:
            print(f"Error Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Request took longer than 10 seconds")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Could not connect to server")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    print("🧪 Testing Form Builder API Endpoints")
    print(f"Backend URL: {BASE_URL}")
    
    # Test core endpoints that FormBuilder uses
    endpoints_to_test = [
        ("/api/forms/field-types", "GET"),
        ("/api/forms/", "GET"),
        ("/api/forms/", "POST", {
            "title": "Test Form API Speed",
            "description": "Testing form creation speed",
            "schema": {
                "version": "1.0",
                "fields": [
                    {
                        "id": "name",
                        "type": "text",
                        "label": "Name",
                        "required": True
                    }
                ]
            }
        })
    ]
    
    for endpoint_data in endpoints_to_test:
        if len(endpoint_data) == 2:
            endpoint, method = endpoint_data
            test_endpoint(endpoint, method)
        else:
            endpoint, method, data = endpoint_data
            test_endpoint(endpoint, method, data)
    
    print(f"\n{'='*60}")
    print("✅ API Testing Complete")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
