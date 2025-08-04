#!/usr/bin/env python3
"""
Test API endpoints with authentication
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m",  # Green
        "ERROR": "\033[91m",    # Red
        "WARNING": "\033[93m"   # Yellow
    }
    color = status_colors.get(status, "\033[0m")
    reset = "\033[0m"
    print(f"{color}[{timestamp}] {status}: {message}{reset}")

def test_login():
    """Test login to get authentication token"""
    print_status("Testing login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            print_status("✅ Login successful", "SUCCESS")
            return token
        else:
            print_status(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Login failed: {str(e)}", "ERROR")
        return None

def test_forms_with_auth(token):
    """Test forms API with authentication"""
    print_status("Testing forms API with authentication...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/forms", headers=headers)
        if response.status_code == 200:
            forms = response.json()
            print_status(f"✅ Get forms successful: {len(forms.get('forms', []))} forms found", "SUCCESS")
            return forms.get('forms', [])
        else:
            print_status(f"❌ Get forms failed: {response.status_code}", "ERROR")
            return []
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Get forms failed: {str(e)}", "ERROR")
        return []

def test_form_submission_with_auth(token, form_id):
    """Test form submission with authentication"""
    print_status(f"Testing form submission for form {form_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get form details first
    try:
        response = requests.get(f"{API_BASE}/forms/{form_id}", headers=headers)
        if response.status_code == 200:
            form = response.json()
            print_status(f"✅ Got form details: {form.get('title')}", "SUCCESS")
            print_status(f"Form schema: {json.dumps(form.get('schema', {}), indent=2)}", "INFO")
            
            # Create submission data based on form schema
            schema = form.get('schema', {})
            fields = schema.get('fields', [])
            
            submission_data = {
                "data": {},
                "submitter": {
                    "email": "test@example.com"
                }
            }
            
            # Fill in required fields
            for field in fields:
                field_id = field.get('id')
                field_type = field.get('type')
                is_required = field.get('required', False)
                
                if is_required:
                    if field_type == 'text':
                        submission_data["data"][field_id] = "Test User"
                    elif field_type == 'email':
                        submission_data["data"][field_id] = "test@example.com"
                    elif field_type == 'number':
                        submission_data["data"][field_id] = 5
                    elif field_type == 'select':
                        options = field.get('options', [])
                        if options:
                            submission_data["data"][field_id] = options[0]
                    elif field_type == 'radio':
                        options = field.get('options', [])
                        if options:
                            submission_data["data"][field_id] = options[0]
                    elif field_type == 'textarea':
                        submission_data["data"][field_id] = "This is a test submission"
            
            print_status(f"Submission data: {json.dumps(submission_data, indent=2)}", "INFO")
            
            # Submit the form
            response = requests.post(f"{API_BASE}/forms/{form_id}/submissions", json=submission_data, headers=headers)
            if response.status_code == 201:
                result = response.json()
                submission_id = result.get('id')
                print_status(f"✅ Form submission successful: Submission ID {submission_id}", "SUCCESS")
                return submission_id
            else:
                print_status(f"❌ Form submission failed: {response.status_code} - {response.text}", "ERROR")
                return None
        else:
            print_status(f"❌ Get form details failed: {response.status_code}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Form submission failed: {str(e)}", "ERROR")
        return None

def test_automated_reports_with_auth(token):
    """Test automated reports API with authentication"""
    print_status("Testing automated reports API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get reports
    try:
        response = requests.get(f"{API_BASE}/reports/automated", headers=headers)
        if response.status_code == 200:
            reports = response.json()
            print_status(f"✅ Get automated reports successful: {len(reports.get('reports', []))} reports found", "SUCCESS")
        else:
            print_status(f"❌ Get automated reports failed: {response.status_code}", "ERROR")
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Get automated reports failed: {str(e)}", "ERROR")

def main():
    """Main testing function"""
    print_status("🚀 Starting Authenticated API Testing", "INFO")
    print_status("=" * 50, "INFO")
    
    # Test login
    token = test_login()
    if not token:
        print_status("❌ Authentication failed, cannot test protected endpoints", "ERROR")
        return
    
    # Test forms with auth
    forms = test_forms_with_auth(token)
    if forms:
        # Test form submission with the first form
        form_id = forms[0].get('id')
        if form_id:
            test_form_submission_with_auth(token, form_id)
    
    # Test automated reports
    test_automated_reports_with_auth(token)
    
    print_status("=" * 50, "INFO")
    print_status("🎉 Authenticated API Testing Complete!", "SUCCESS")
    print_status("=" * 50, "INFO")

if __name__ == "__main__":
    main() 