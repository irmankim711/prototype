#!/usr/bin/env python3
"""
Test script for the new form data export endpoints
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_form_data_endpoints():
    """Test the new form data export endpoints"""
    
    print("🧪 Testing Form Data Export Endpoints")
    print("=" * 50)
    
    # Test 1: Fetch form data (GET endpoint)
    print("\n1️⃣ Testing GET /api/forms/{form_id}/fetch-data")
    try:
        response = requests.get(
            f"{API_BASE}/forms/1/fetch-data",
            params={
                "page": 1,
                "per_page": 10,
                "include_metadata": True,
                "include_analytics": True
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists (requires authentication)")
        elif response.status_code == 200:
            print("   ✅ Endpoint working successfully")
            data = response.json()
            print(f"   📊 Form: {data.get('form', {}).get('title', 'N/A')}")
            print(f"   📝 Submissions: {data.get('pagination', {}).get('total', 0)}")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - make sure backend is running")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Export form data to Excel (POST endpoint)
    print("\n2️⃣ Testing POST /api/forms/{form_id}/fetch-data-excel")
    try:
        export_data = {
            "include_analytics": True,
            "date_range": {
                "start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end": datetime.now().strftime("%Y-%m-%d")
            },
            "filters": {
                "status": "submitted"
            },
            "excel_options": {
                "include_form_schema": True,
                "include_submission_metadata": True,
                "formatting": "professional",
                "compression": True
            }
        }
        
        response = requests.post(
            f"{API_BASE}/forms/1/fetch-data-excel",
            json=export_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists (requires authentication)")
        elif response.status_code == 200:
            print("   ✅ Endpoint working successfully")
            data = response.json()
            print(f"   📊 Export successful: {data.get('message', 'N/A')}")
        elif response.status_code == 404:
            print("   ⚠️  Form not found (expected if no forms exist)")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - make sure backend is running")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Check if endpoints are registered
    print("\n3️⃣ Checking endpoint registration")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   ⚠️  Backend responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend is not running")
        print("   💡 Start your backend server first:")
        print("      cd backend && python app.py")
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("   1. Make sure your backend server is running")
    print("   2. Navigate to /form-data-export-demo in your frontend")
    print("   3. Test the export functionality with a real form")
    print("   4. Check the browser console for any errors")

if __name__ == "__main__":
    test_form_data_endpoints()
