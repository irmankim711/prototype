#!/usr/bin/env python3
"""
Test script for the Excel report generation endpoint
"""

import requests
import json
from pathlib import Path

def test_excel_endpoint():
    """Test the Excel report generation endpoint"""
    
    # Test data
    test_data = {
        "excelFilePath": "app/static/uploads/excel/1_4e90e4bc904b45d5ac93a42c35b5ae33_SENARAI SEMAK PUNCAK ALAM.xlsx",
        "templateId": "Temp1.docx",
        "reportTitle": "Test Report"
    }
    
    # Test the endpoint
    url = "http://localhost:5000/api/v1/nextgen/excel/generate-report"
    
    print(f"🔍 Testing endpoint: {url}")
    print(f"📊 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        # First, let's check if the endpoint exists
        response = requests.options(url)
        print(f"📡 OPTIONS response: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        # Now try the POST request
        response = requests.post(url, json=test_data)
        
        print(f"📡 POST response status: {response.status_code}")
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
                
    except requests.exceptions.ConnectionError:
        print("🚨 Connection error - server not running")
    except Exception as e:
        print(f"🚨 Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_excel_endpoint()
