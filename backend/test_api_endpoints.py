#!/usr/bin/env python3
"""
Comprehensive API Testing Script for the Report Generation Platform
Tests all endpoints to ensure they're working correctly
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

TEST_FORM = {
    "title": "Test Employee Survey",
    "description": "Test form for API testing",
    "schema": {
        "fields": [
            {
                "id": "name",
                "label": "Full Name",
                "type": "text",
                "required": True,
                "order": 1
            },
            {
                "id": "satisfaction",
                "label": "Job Satisfaction",
                "type": "number",
                "required": True,
                "order": 2
            },
            {
                "id": "feedback",
                "label": "Feedback",
                "type": "textarea",
                "required": False,
                "order": 3
            }
        ]
    },
    "is_active": True,
    "is_public": True
}

TEST_SUBMISSION = {
    "data": {
        "name": "John Doe",
        "satisfaction": 8,
        "feedback": "Great working environment!"
    },
    "submitter": {
        "email": "john.doe@example.com"
    },
    "source": "test"
}

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

def test_authentication():
    """Test authentication endpoints"""
    print_status("Testing authentication endpoints...")
    
    # Test login
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=TEST_USER)
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

def test_forms_api(token):
    """Test forms API endpoints"""
    print_status("Testing forms API endpoints...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # Test get forms
    try:
        response = requests.get(f"{API_BASE}/forms", headers=headers)
        if response.status_code == 200:
            forms = response.json()
            print_status(f"✅ Get forms successful: {len(forms.get('forms', []))} forms found", "SUCCESS")
        else:
            print_status(f"❌ Get forms failed: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Get forms failed: {str(e)}", "ERROR")
        return False
    
    # Test create form
    try:
        response = requests.post(f"{API_BASE}/forms", json=TEST_FORM, headers=headers)
        if response.status_code == 201:
            form_data = response.json()
            form_id = form_data.get('id')
            print_status(f"✅ Create form successful: Form ID {form_id}", "SUCCESS")
            return form_id
        else:
            print_status(f"❌ Create form failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Create form failed: {str(e)}", "ERROR")
        return None

def test_form_submission(form_id, token):
    """Test form submission endpoint"""
    print_status("Testing form submission endpoint...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    submission_data = {
        "form_id": form_id,
        "data": TEST_SUBMISSION["data"],
        "submitter": TEST_SUBMISSION["submitter"],
        "source": TEST_SUBMISSION["source"]
    }
    
    try:
        response = requests.post(f"{API_BASE}/forms/submit", json=submission_data, headers=headers)
        if response.status_code == 201:
            submission_result = response.json()
            submission_id = submission_result.get('submission_id')
            print_status(f"✅ Form submission successful: Submission ID {submission_id}", "SUCCESS")
            return submission_id
        else:
            print_status(f"❌ Form submission failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Form submission failed: {str(e)}", "ERROR")
        return None

def test_automated_reports_api(form_id, token):
    """Test automated reports API endpoints"""
    print_status("Testing automated reports API endpoints...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
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
    
    # Test generate report
    generate_data = {
        "form_id": form_id,
        "report_type": "summary",
        "date_range": "last_30_days"
    }
    
    try:
        response = requests.post(f"{API_BASE}/reports/automated/generate", json=generate_data, headers=headers)
        if response.status_code == 202:
            result = response.json()
            task_id = result.get('task_id')
            print_status(f"✅ Generate report successful: Task ID {task_id}", "SUCCESS")
            return task_id
        else:
            print_status(f"❌ Generate report failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Generate report failed: {str(e)}", "ERROR")
        return None

def test_report_status(task_id, token):
    """Test report status endpoint"""
    if not task_id:
        print_status("⚠️ Skipping status check - no task ID", "WARNING")
        return
    
    print_status("Testing report status endpoint...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(f"{API_BASE}/reports/automated/status/{task_id}", headers=headers)
        if response.status_code == 200:
            status_data = response.json()
            status = status_data.get('status')
            print_status(f"✅ Report status check successful: Status {status}", "SUCCESS")
            return status
        else:
            print_status(f"❌ Report status check failed: {response.status_code}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Report status check failed: {str(e)}", "ERROR")
        return None

def test_form_submissions_api(form_id, token):
    """Test form submissions API"""
    print_status("Testing form submissions API...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(f"{API_BASE}/forms/{form_id}/submissions", headers=headers)
        if response.status_code == 200:
            submissions = response.json()
            print_status(f"✅ Get form submissions successful: {len(submissions.get('submissions', []))} submissions found", "SUCCESS")
            return True
        else:
            print_status(f"❌ Get form submissions failed: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Get form submissions failed: {str(e)}", "ERROR")
        return False

def main():
    """Main testing function"""
    print_status("🚀 Starting API Endpoint Testing", "INFO")
    print_status("=" * 50, "INFO")
    
    # Test health check
    if not test_health_check():
        print_status("❌ Backend is not running. Please start the Flask server first.", "ERROR")
        sys.exit(1)
    
    # Test authentication
    token = test_authentication()
    if not token:
        print_status("⚠️ Authentication failed, continuing with public endpoints", "WARNING")
    
    # Test forms API
    form_id = test_forms_api(token)
    if not form_id:
        print_status("❌ Forms API test failed", "ERROR")
        return
    
    # Test form submission
    submission_id = test_form_submission(form_id, token)
    if not submission_id:
        print_status("❌ Form submission test failed", "ERROR")
        return
    
    # Test form submissions API
    test_form_submissions_api(form_id, token)
    
    # Test automated reports API
    task_id = test_automated_reports_api(form_id, token)
    
    # Test report status
    if task_id:
        print_status("⏳ Waiting 5 seconds before checking report status...", "INFO")
        time.sleep(5)
        test_report_status(task_id, token)
    
    print_status("=" * 50, "INFO")
    print_status("🎉 API Testing Complete!", "SUCCESS")
    print_status("=" * 50, "INFO")

if __name__ == "__main__":
    main() 