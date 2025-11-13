#!/usr/bin/env python3
"""
Test script for the Excel report generation endpoint with authentication
"""

import requests
import json
from pathlib import Path

def test_excel_endpoint_with_auth():
    """Test the Excel report generation endpoint with authentication"""
    
    base_url = "http://localhost:5000"
    
    # Step 1: Login to get a token
    print("🔐 Step 1: Authenticating user...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"  # Updated password
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"📡 Login response status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print("✅ Login successful!")
            
            # Extract token
            access_token = login_result.get('access_token')
            if not access_token:
                print("❌ No access token in login response")
                print(f"📄 Login response: {json.dumps(login_result, indent=2)}")
                return
            
            print(f"🔑 Got access token: {access_token[:20]}...")
            
            # Step 2: Test the Excel endpoint with authentication
            print("\n🔍 Step 2: Testing Excel endpoint with authentication...")
            
            test_data = {
                "excelFilePath": "app/static/uploads/excel/1_4e90e4bc904b45d5ac93a42c35b5ae33_SENARAI SEMAK PUNCAK ALAM.xlsx",
                "templateId": "Temp1.docx",
                "reportTitle": "Test Report"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{base_url}/api/v1/nextgen/excel/generate-report"
            
            print(f"🔗 Testing endpoint: {url}")
            print(f"📊 Test data: {json.dumps(test_data, indent=2)}")
            print(f"🔑 Using token: {access_token[:20]}...")
            
            response = requests.post(url, json=test_data, headers=headers)
            
            print(f"📡 Response status: {response.status_code}")
            print(f"📋 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Success!")
                print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"🚨 Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"🚨 Error text: {response.text}")
                    
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            try:
                error_data = login_response.json()
                print(f"🚨 Login error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"🚨 Login error text: {login_response.text}")
                
    except requests.exceptions.ConnectionError:
        print("🚨 Connection error - server not running")
    except Exception as e:
        print(f"🚨 Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_excel_endpoint_with_auth()
