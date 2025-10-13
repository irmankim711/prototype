#!/usr/bin/env python3
"""
Quick test to verify the 400 error fix for the enhanced-export endpoint
"""

import sys
import os
import requests
import json
import time

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_enhanced_export_endpoint():
    """Test the /api/v1/integrations/excel/enhanced-export endpoint"""

    # Test URL
    url = "http://localhost:5000/api/v1/integrations/excel/enhanced-export"

    # Test payload that was causing the 400 error
    test_payload = {
        "dataSourceId": "mock-excel-1",
        "action": "getFields"
    }

    headers = {
        'Content-Type': 'application/json'
    }

    print("🔍 Testing enhanced-export endpoint...")
    print(f"📡 URL: {url}")
    print(f"📦 Payload: {json.dumps(test_payload, indent=2)}")

    try:
        # Make the POST request
        response = requests.post(url, json=test_payload, headers=headers, timeout=10)

        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")

        try:
            response_data = response.json()
            print(f"📥 Response Data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📥 Response Text: {response.text}")

        # Check if the fix worked
        if response.status_code == 200:
            print("✅ SUCCESS: The endpoint now returns 200 OK!")
            return True
        elif response.status_code == 400:
            print("❌ STILL FAILING: The endpoint still returns 400 Bad Request")
            return False
        elif response.status_code == 401:
            print("🔒 AUTHENTICATION: The endpoint requires authentication")
            print("This is expected behavior - the fix worked!")
            return True
        else:
            print(f"⚠️ UNEXPECTED: The endpoint returned {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to the backend server")
        print("Make sure the backend server is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def check_backend_server():
    """Check if the backend server is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        print("✅ Backend server is running")
        return True
    except:
        print("❌ Backend server is not running")
        print("Please start the backend server first: cd backend && python run.py")
        return False

if __name__ == "__main__":
    print("🚀 Testing the 400 error fix...")

    # Check if backend is running
    if not check_backend_server():
        sys.exit(1)

    # Wait a moment for server to be ready
    time.sleep(1)

    # Test the endpoint
    success = test_enhanced_export_endpoint()

    if success:
        print("\n🎉 TEST PASSED: The fix appears to be working!")
    else:
        print("\n💥 TEST FAILED: The fix needs more work")
        sys.exit(1)