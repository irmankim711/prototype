#!/usr/bin/env python3
"""
Test script to debug the 500 error in Excel report generation endpoint
"""

import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5001"
API_ENDPOINT = f"{BASE_URL}/api/v1/nextgen/excel/generate-report"

def test_excel_report_generation():
    """
    Test the Excel report generation endpoint manually to isolate the 500 error
    """
    print("🔍 Testing Excel Report Generation Endpoint")
    print(f"📡 Endpoint: {API_ENDPOINT}")
    
    # Test payload (matching what frontend sends)
    test_payload = {
        "excelFilePath": "/path/to/test/excel/file.xlsx",  # This will likely fail, but we want to see HOW it fails
        "templateId": "test_template",
        "reportTitle": "Test Report - Manual API Call"
    }
    
    print(f"📦 Test payload: {json.dumps(test_payload, indent=2)}")
    
    # Test 1: Basic connectivity (no auth)
    print("\n🔄 Test 1: Basic connectivity test (expecting 401 - no auth)")
    try:
        response = requests.post(API_ENDPOINT, json=test_payload, timeout=10)
        print(f"✅ Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        print(f"📝 Response content: {response.text[:500]}")
        
        if response.status_code == 401:
            print("✅ Expected 401 - endpoint is accessible but requires authentication")
        elif response.status_code == 404:
            print("❌ 404 - endpoint not found, check URL and route registration")
        elif response.status_code == 500:
            print("❌ 500 - internal server error even without auth (bad)")
        else:
            print(f"ℹ️ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("🔍 Is the backend server running on localhost:5001?")
        return False
    
    # Test 2: Check if the route exists using OPTIONS
    print("\n🔄 Test 2: OPTIONS request to check if route exists")
    try:
        response = requests.options(API_ENDPOINT, timeout=10)
        print(f"✅ OPTIONS response status: {response.status_code}")
        print(f"📄 Allowed methods: {response.headers.get('Allow', 'Not specified')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ OPTIONS request failed: {e}")
    
    # Test 3: Try other similar endpoints to see if they work
    print("\n🔄 Test 3: Testing related endpoints")
    related_endpoints = [
        f"{BASE_URL}/api/v1/nextgen/excel/upload",
        f"{BASE_URL}/api/v1/nextgen/templates",
        f"{BASE_URL}/api/v1/health",
        f"{BASE_URL}/health",
        f"{BASE_URL}/api/health"
    ]
    
    for endpoint in related_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"📍 {endpoint}: {response.status_code}")
        except:
            print(f"📍 {endpoint}: ❌ Failed")
    
    # Test 4: Test with invalid JSON to see error handling
    print("\n🔄 Test 4: Test with invalid JSON payload")
    try:
        response = requests.post(API_ENDPOINT, data="invalid json", timeout=10)
        print(f"✅ Invalid JSON response status: {response.status_code}")
        print(f"📝 Invalid JSON response: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Invalid JSON test failed: {e}")
    
    # Test 5: Test with empty payload
    print("\n🔄 Test 5: Test with empty JSON payload")
    try:
        response = requests.post(API_ENDPOINT, json={}, timeout=10)
        print(f"✅ Empty payload response status: {response.status_code}")
        print(f"📝 Empty payload response: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Empty payload test failed: {e}")
    
    print("\n🏁 Manual endpoint testing completed!")
    return True

def check_backend_status():
    """
    Check if backend is running and responsive
    """
    print("\n🔍 Checking backend status...")
    
    # Try common health check endpoints
    health_endpoints = [
        f"{BASE_URL}/health",
        f"{BASE_URL}/api/health", 
        f"{BASE_URL}/api/v1/health",
        f"{BASE_URL}/"
    ]
    
    for endpoint in health_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"📝 Response: {response.text[:100]}")
                return True
        except:
            print(f"❌ {endpoint}: Not accessible")
    
    print("❌ Backend appears to be down or not accessible")
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Excel Report Generation Debug Script")
    print("=" * 60)
    
    # Check backend status first
    if check_backend_status():
        # Run the actual tests
        test_excel_report_generation()
    else:
        print("\n⚠️ Backend is not accessible. Please:")
        print("1. Start the backend server (flask run or python app.py)")
        print("2. Ensure it's running on localhost:5001")
        print("3. Check for any startup errors in backend logs")
    
    print("\n" + "=" * 60)
    print("📋 Next Steps:")
    print("1. Check backend terminal/logs for detailed error messages")
    print("2. Verify the exact payload being sent from frontend")
    print("3. Test with valid Excel file paths and template IDs") 
    print("4. Check database connectivity and migrations")
    print("=" * 60)
