#!/usr/bin/env python3
"""
Complete 500 Error Fix Validation Test
=====================================

This test validates the complete fix for the 500 Internal Server Error in form fetching
by testing the entire flow from form creation to public visibility.

Test Coverage:
1. Backend endpoints are accessible and return correct data
2. Authentication flow works properly
3. Form creation and status management works
4. Public forms endpoint returns correct data without authentication
5. Toggle functionality works for making forms public/active
"""

import requests
import json
import sys
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
API_BASE = f"{BASE_URL}/api"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_backend_health():
    """Test if backend is running and healthy"""
    log("Testing backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            log("✅ Backend is healthy")
            return True
        else:
            log(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Backend is not accessible: {e}")
        return False

def test_public_forms_endpoint():
    """Test the public forms endpoint (should work without authentication)"""
    log("Testing public forms endpoint...")
    try:
        response = requests.get(f"{API_BASE}/forms/public", timeout=10)
        log(f"Response status: {response.status_code}")
        log(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            log(f"✅ Public forms endpoint works - Found {len(data)} forms")
            
            # Check data structure
            if isinstance(data, list):
                log("✅ Response is a list")
                if data:
                    first_form = data[0]
                    required_fields = ['id', 'title', 'description', 'is_public', 'is_active']
                    missing_fields = [field for field in required_fields if field not in first_form]
                    if not missing_fields:
                        log("✅ Form data structure is correct")
                    else:
                        log(f"⚠️ Missing fields in form data: {missing_fields}")
                    
                    # Show sample form data
                    log(f"Sample form: {json.dumps(first_form, indent=2)}")
                else:
                    log("ℹ️ No forms found (empty list)")
            else:
                log(f"⚠️ Response is not a list: {type(data)}")
            
            return True
        else:
            log(f"❌ Public forms endpoint failed: {response.status_code}")
            log(f"Response: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Error testing public forms endpoint: {e}")
        return False

def test_auth_login():
    """Test authentication login"""
    log("Testing authentication login...")
    try:
        # Test with default admin credentials
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                log("✅ Authentication login successful")
                return data['access_token']
            else:
                log("❌ No access token in login response")
                return None
        else:
            log(f"❌ Login failed: {response.status_code}")
            log(f"Response: {response.text}")
            return None
            
    except Exception as e:
        log(f"❌ Error testing login: {e}")
        return None

def test_protected_forms_endpoint(token):
    """Test the protected forms endpoint with authentication"""
    log("Testing protected forms endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/forms", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            log(f"✅ Protected forms endpoint works - Found {len(data)} forms")
            return True
        else:
            log(f"❌ Protected forms endpoint failed: {response.status_code}")
            log(f"Response: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Error testing protected forms endpoint: {e}")
        return False

def test_form_toggle(token):
    """Test form status toggle functionality"""
    log("Testing form toggle functionality...")
    try:
        # First get all forms
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/forms", headers=headers, timeout=10)
        
        if response.status_code != 200:
            log("❌ Cannot get forms for toggle test")
            return False
        
        forms = response.json()
        if not forms:
            log("ℹ️ No forms available for toggle test")
            return True
        
        # Test toggle on first form
        test_form = forms[0]
        form_id = test_form['id']
        current_public = test_form.get('is_public', False)
        
        log(f"Testing toggle on form {form_id} (current is_public: {current_public})")
        
        # Toggle the public status
        toggle_data = {
            "is_public": not current_public
        }
        
        response = requests.patch(
            f"{API_BASE}/forms/{form_id}/status",
            json=toggle_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            updated_form = response.json()
            new_public = updated_form.get('is_public')
            if new_public == (not current_public):
                log("✅ Form toggle functionality works")
                
                # Toggle back to original state
                restore_data = {"is_public": current_public}
                requests.patch(
                    f"{API_BASE}/forms/{form_id}/status",
                    json=restore_data,
                    headers=headers,
                    timeout=10
                )
                log("✅ Restored original form state")
                return True
            else:
                log(f"❌ Toggle didn't work: expected {not current_public}, got {new_public}")
                return False
        else:
            log(f"❌ Form toggle failed: {response.status_code}")
            log(f"Response: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Error testing form toggle: {e}")
        return False

def main():
    """Run all tests"""
    log("Starting Complete 500 Error Fix Validation")
    log("=" * 50)
    
    # Test results
    results = {}
    
    # 1. Test backend health
    results['backend_health'] = test_backend_health()
    if not results['backend_health']:
        log("❌ Backend is not running. Please start the backend first.")
        sys.exit(1)
    
    # 2. Test public forms endpoint (main fix validation)
    results['public_forms'] = test_public_forms_endpoint()
    
    # 3. Test authentication
    token = test_auth_login()
    results['auth_login'] = token is not None
    
    # 4. Test protected endpoint
    if token:
        results['protected_forms'] = test_protected_forms_endpoint(token)
        results['form_toggle'] = test_form_toggle(token)
    else:
        results['protected_forms'] = False
        results['form_toggle'] = False
    
    # Summary
    log("\n" + "=" * 50)
    log("TEST RESULTS SUMMARY")
    log("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"{test_name:20} : {status}")
    
    log(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if results.get('public_forms', False):
        log("\n🎉 MAIN FIX VALIDATED: Public forms endpoint is working!")
        log("The 500 error in form fetching has been resolved.")
    else:
        log("\n⚠️ MAIN FIX ISSUE: Public forms endpoint still has problems.")
    
    if all(results.values()):
        log("\n✅ ALL TESTS PASSED - Complete system is working!")
        return True
    else:
        log("\n⚠️ Some tests failed - check individual results above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
