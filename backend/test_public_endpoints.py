#!/usr/bin/env python3
"""
Test Public API Endpoints (No Authentication Required)
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

def test_health_check():
    """Test basic health check endpoint"""
    print_status("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_status("✅ Health check passed", "SUCCESS")
            return True
        else:
            print_status(f"❌ Health check failed: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Health check failed: {str(e)}", "ERROR")
        return False

def test_public_forms():
    """Test public forms endpoint"""
    print_status("Testing public forms endpoint...")
    try:
        response = requests.get(f"{API_BASE}/forms/public")
        if response.status_code == 200:
            forms = response.json()
            print_status(f"✅ Public forms successful: {len(forms)} forms found", "SUCCESS")
            print_status(f"Forms data: {json.dumps(forms, indent=2)}", "INFO")
            return forms
        else:
            print_status(f"❌ Public forms failed: {response.status_code}", "ERROR")
            return []
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Public forms failed: {str(e)}", "ERROR")
        return []

def test_form_submission_without_auth():
    """Test form submission without authentication"""
    print_status("Testing form submission (public endpoint)...")
    
    # First, get available forms
    forms = test_public_forms()
    if not forms:
        print_status("⚠️ No forms available for submission test", "WARNING")
        return None
    
    # Use the first form for testing
    if isinstance(forms, list) and len(forms) > 0:
        form = forms[0]
        form_id = form.get('id')
    elif isinstance(forms, dict) and 'forms' in forms:
        form = forms['forms'][0]
        form_id = form.get('id')
    else:
        print_status("⚠️ No forms available for submission test", "WARNING")
        return None
    
    # Get form schema to create proper submission data
    form_schema = form.get('schema', {})
    fields = form_schema.get('fields', [])
    
    # Create submission data based on form fields
    submission_data = {
        "data": {},
        "submitter": {
            "email": "test@example.com"
        }
    }
    
    # Fill in required fields based on form schema
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
    
    print_status(f"Form schema: {json.dumps(form_schema, indent=2)}", "INFO")
    
    try:
        print_status(f"Submitting to: {API_BASE}/forms/{form_id}/submissions", "INFO")
        print_status(f"Data: {json.dumps(submission_data, indent=2)}", "INFO")
        response = requests.post(f"{API_BASE}/forms/{form_id}/submissions", json=submission_data)
        print_status(f"Response status: {response.status_code}", "INFO")
        print_status(f"Response text: {response.text}", "INFO")
        if response.status_code == 201:
            result = response.json()
            submission_id = result.get('submission_id')
            print_status(f"✅ Form submission successful: Submission ID {submission_id}", "SUCCESS")
            return submission_id
        else:
            print_status(f"❌ Form submission failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Form submission failed: {str(e)}", "ERROR")
        return None

def test_available_endpoints():
    """Test what endpoints are available"""
    print_status("Testing available endpoints...")
    
    endpoints_to_test = [
        ("GET", "/health", "Health check"),
        ("GET", "/api/forms/public", "Public forms"),
        ("POST", "/api/forms/submit", "Form submission"),
        ("GET", "/api/reports", "Reports (requires auth)"),
        ("GET", "/api/forms", "Forms (requires auth)"),
    ]
    
    for method, endpoint, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}")
            
            status = "✅" if response.status_code in [200, 201, 202] else "❌"
            auth_required = "🔒" if response.status_code == 401 else ""
            print_status(f"{status} {method} {endpoint} - {response.status_code} {auth_required}", 
                        "SUCCESS" if response.status_code in [200, 201, 202] else "ERROR")
        except requests.exceptions.RequestException as e:
            print_status(f"❌ {method} {endpoint} - Connection failed: {str(e)}", "ERROR")

def main():
    """Main testing function"""
    print_status("🚀 Starting Public API Endpoint Testing", "INFO")
    print_status("=" * 50, "INFO")
    
    # Test health check
    if not test_health_check():
        print_status("❌ Backend is not running. Please start the Flask server first.", "ERROR")
        return
    
    # Test available endpoints
    test_available_endpoints()
    
    # Test public forms
    forms = test_public_forms()
    
    # Test form submission
    if forms:
        test_form_submission_without_auth()
    
    print_status("=" * 50, "INFO")
    print_status("🎉 Public API Testing Complete!", "SUCCESS")
    print_status("=" * 50, "INFO")

if __name__ == "__main__":
    main() 