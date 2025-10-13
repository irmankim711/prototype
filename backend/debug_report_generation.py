#!/usr/bin/env python3
"""
Debug Report Generation Endpoint
Test the specific endpoint that's failing with 500 error
"""

import sys
import os
import requests
import json
sys.path.append('.')

def test_report_generation_endpoint():
    """Test the failing report generation endpoint"""
    print("🔍 Debugging Report Generation Endpoint")
    print("=" * 50)
    
    # Backend URL
    backend_url = "http://127.0.0.1:5001"
    endpoint = "/api/v1/nextgen/excel/generate-report"
    
    print(f"🎯 Testing: {backend_url}{endpoint}")
    
    # Test data (minimal payload to avoid complex errors)
    test_payload = {
        "templateId": "d88443ff-efce-46ef-89ea-c7cdd6608950",  # Standard Business Report
        "title": "Debug Test Report",
        "excelDataSource": "mock-excel-1",
        "generateCharts": True,
        "includeAnalytics": False,
        "reportFormat": "pdf"
    }
    
    print(f"📊 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        # First test without authentication (might be the issue)
        print("\n🔓 Testing without authentication...")
        response = requests.post(
            f"{backend_url}{endpoint}",
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print("❌ Authentication required - this is the issue!")
            print("🔐 Need to implement JWT token or disable auth for testing")
            
            # Check if there's a health endpoint without auth
            health_response = requests.get(f"{backend_url}/api/reports/health")
            if health_response.status_code == 200:
                print("✅ Health endpoint works without auth")
                print("💡 Suggestion: Test with JWT token or temporarily disable @jwt_required()")
        
        elif response.status_code == 500:
            print("❌ Internal Server Error (500)")
            try:
                error_data = response.json()
                print(f"📄 Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Raw Response: {response.text}")
                
        elif response.status_code == 404:
            print("❌ Endpoint not found (404)")
            print("🔍 Check if the route is properly registered")
            
        else:
            print(f"📊 Unexpected status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend server running?")
        print("🚀 Start backend with: cd backend && python run.py")
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout - endpoint is taking too long")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_auth_requirements():
    """Test what authentication is needed"""
    print("\n🔐 Testing Authentication Requirements")
    print("-" * 40)
    
    backend_url = "http://127.0.0.1:5001"
    
    # Test various endpoints to understand auth patterns
    test_endpoints = [
        "/api/reports/health",
        "/api/v1/nextgen/data-sources", 
        "/api/v1/nextgen/templates",
        "/health"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=10)
            print(f"📊 {endpoint}: {response.status_code}")
            if response.status_code == 401:
                print(f"   🔐 Requires authentication")
            elif response.status_code == 200:
                print(f"   ✅ Public endpoint")
            elif response.status_code == 404:
                print(f"   ❓ Not found")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def suggest_fixes():
    """Suggest potential fixes for the issue"""
    print("\n💡 POTENTIAL FIXES:")
    print("=" * 30)
    
    print("1. 🔐 AUTHENTICATION ISSUE (Most Likely):")
    print("   - The endpoint requires @jwt_required()")
    print("   - Frontend needs to send proper JWT token")
    print("   - Check if login/auth is working in frontend")
    print("   - Temporarily disable @jwt_required() for testing")
    
    print("\n2. 📊 DATA VALIDATION:")
    print("   - Check if required fields are missing in request")
    print("   - Verify templateId exists in database")
    print("   - Ensure Excel data source is valid")
    
    print("\n3. 🗄️ DATABASE/MODEL ISSUES:")
    print("   - Check if User model exists and is working")
    print("   - Verify Report model can be created")
    print("   - Ensure database connection is stable")
    
    print("\n4. 📁 FILE/PATH ISSUES:")
    print("   - Check if upload directories exist")
    print("   - Verify Excel files are accessible")
    print("   - Ensure template files are found")
    
    print("\n🔧 IMMEDIATE DEBUGGING STEPS:")
    print("1. Check backend logs for full error stacktrace")
    print("2. Test with Postman/curl with proper JWT token")
    print("3. Temporarily add logging to the endpoint")
    print("4. Verify database connection and model creation")

def main():
    print("🚀 Report Generation Debug Tool")
    print("=" * 60)
    
    test_report_generation_endpoint()
    test_auth_requirements()
    suggest_fixes()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Check the backend logs for the full error")
    print("2. Look at the browser network tab for request details")
    print("3. Test authentication first")
    print("4. If needed, we can temporarily disable @jwt_required() for testing")

if __name__ == "__main__":
    main()