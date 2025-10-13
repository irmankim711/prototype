#!/usr/bin/env python3
"""
Test AI Text Enhancement Endpoints
Tests the new AI-powered text enhancement features
"""

import requests
import json
import os
import sys

# Add backend to path
sys.path.append('backend')

BASE_URL = "http://localhost:5000/api/v1/nextgen"

def test_with_auth():
    """Test with authentication"""
    
    # Test credentials  
    test_email = "admin@example.com"
    test_password = "admin123"
    
    print("🔐 Testing AI Text Enhancement Endpoints...")
    print("=" * 50)
    
    # 1. Login to get token
    print("\n1️⃣ Logging in...")
    login_response = requests.post("http://localhost:5000/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    
    if login_response.status_code != 200:
        print("❌ Login failed. Creating test user...")
        # Try to create user
        register_response = requests.post("http://localhost:5000/api/auth/register", json={
            "name": "Test User",
            "email": test_email,
            "password": test_password
        })
        if register_response.status_code == 201:
            print("✅ User created, logging in again...")
            login_response = requests.post("http://localhost:5000/api/auth/login", json={
                "email": test_email,
                "password": test_password
            })
        else:
            print(f"❌ Failed to create user: {register_response.text}")
            return
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
        
    token = login_response.json().get('access_token')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("✅ Successfully logged in!")
    
    # 2. Test AI Text Enhancement
    print("\n2️⃣ Testing AI Text Enhancement...")
    
    test_text = "This report shows the results of our analysis. The data indicates some interesting findings."
    
    enhancement_tests = [
        {"type": "improve", "description": "General improvement"},
        {"type": "formal", "description": "Make more formal"},
        {"type": "summary", "description": "Create summary"},
        {"type": "expand", "description": "Expand with detail"}
    ]
    
    for test in enhancement_tests:
        print(f"\n  Testing {test['description']}...")
        response = requests.post(f"{BASE_URL}/ai/enhance-text", 
            headers=headers,
            json={
                "text": test_text,
                "type": test["type"],
                "context": "report"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"  ✅ {test['description']}: {data.get('ai_powered', 'N/A')} AI powered")
                if data.get('enhanced_text'):
                    print(f"     Enhanced: {data['enhanced_text'][:100]}...")
                if data.get('message'):
                    print(f"     Message: {data['message']}")
            else:
                print(f"  ❌ Enhancement failed: {data}")
        else:
            print(f"  ❌ HTTP Error: {response.status_code} - {response.text}")
    
    # 3. Test AI Suggestions
    print("\n3️⃣ Testing AI Suggestions...")
    
    suggestion_response = requests.post(f"{BASE_URL}/ai/suggestions",
        headers=headers,
        json={
            "text": test_text,
            "context": "report"
        }
    )
    
    if suggestion_response.status_code == 200:
        data = suggestion_response.json()
        if data.get('success'):
            suggestions = data.get('suggestions', [])
            print(f"✅ Got {len(suggestions)} suggestions (AI powered: {data.get('ai_powered', 'N/A')})")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"  {i}. [{suggestion.get('category', 'N/A')}] {suggestion.get('suggestion', 'N/A')[:80]}...")
        else:
            print(f"❌ Suggestions failed: {data}")
    else:
        print(f"❌ HTTP Error: {suggestion_response.status_code} - {suggestion_response.text}")
    
    # 4. Test Translation
    print("\n4️⃣ Testing AI Translation...")
    
    translate_response = requests.post(f"{BASE_URL}/ai/translate-text",
        headers=headers,
        json={
            "text": "Hello, this is a test report.",
            "target_language": "Malay",
            "source_language": "English"
        }
    )
    
    if translate_response.status_code == 200:
        data = translate_response.json()
        if data.get('success'):
            print(f"✅ Translation successful (AI powered: {data.get('ai_powered', 'N/A')})")
            if data.get('translated_text'):
                print(f"   Translated: {data['translated_text']}")
        else:
            print(f"❌ Translation failed: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ HTTP Error: {translate_response.status_code} - {translate_response.text}")
    
    # 5. Test Report Content Viewing (if any reports exist)
    print("\n5️⃣ Testing Report Content API...")
    
    # First, let's see if we can create a simple report for testing
    try:
        # Create a test report using the nextgen endpoint
        import tempfile
        import pandas as pd
        
        # Create a simple test Excel file
        test_data = {
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25, 30, 35],
            'Department': ['IT', 'HR', 'Finance']
        }
        df = pd.DataFrame(test_data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            df.to_excel(tmp_file.name, index=False)
            
            # Upload and generate report
            with open(tmp_file.name, 'rb') as f:
                files = {'excel_file': f}
                data = {
                    'template_id': 1,
                    'report_title': 'AI Enhancement Test Report'
                }
                
                report_response = requests.post(f"{BASE_URL}/excel/generate-report",
                    headers={'Authorization': f'Bearer {token}'},
                    files=files,
                    data=data
                )
                
                if report_response.status_code == 200:
                    report_data = report_response.json()
                    if report_data.get('success'):
                        report_id = report_data.get('report_id')
                        print(f"✅ Created test report with ID: {report_id}")
                        
                        # Now test viewing the report content
                        view_response = requests.get(f"{BASE_URL}/reports/{report_id}/view",
                            headers=headers
                        )
                        
                        if view_response.status_code == 200:
                            view_data = view_response.json()
                            if view_data.get('success'):
                                report = view_data.get('report', {})
                                print(f"✅ Successfully viewed report content")
                                print(f"   Title: {report.get('title', 'N/A')}")
                                print(f"   Status: {report.get('status', 'N/A')}")
                                print(f"   LaTeX content length: {len(report.get('latex_content', ''))}")
                            else:
                                print(f"❌ Failed to view report: {view_data}")
                        else:
                            print(f"❌ View report HTTP Error: {view_response.status_code}")
                    else:
                        print(f"❌ Report creation failed: {report_data}")
                else:
                    print(f"❌ Report creation HTTP Error: {report_response.status_code}")
            
            # Clean up temp file
            os.unlink(tmp_file.name)
            
    except Exception as e:
        print(f"⚠️ Report testing skipped: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 AI Text Enhancement Testing Complete!")

if __name__ == "__main__":
    test_with_auth()