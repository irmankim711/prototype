#!/usr/bin/env python3
"""
MVP Feature Test Script
Tests all the core MVP functionality we've implemented.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

class MVPTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        
    def test_auth(self):
        """Test authentication system."""
        print("🔐 Testing Authentication...")
        
        # Test registration (if user doesn't exist)
        register_data = {
            "email": "mvptest@example.com",
            "password": "testpass123",
            "first_name": "MVP",
            "last_name": "Test"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✅ User registration successful")
        elif response.status_code == 409:
            print("ℹ️  User already exists, continuing with login test")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(response.text)
        
        # Test login
        login_data = {
            "email": "mvptest@example.com",
            "password": "testpass123"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print("✅ User login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return False
    
    def test_user_profile(self):
        """Test user profile management."""
        print("\n👤 Testing User Profile...")
        
        # Get profile
        response = self.session.get(f"{BASE_URL}/api/users/profile")
        if response.status_code == 200:
            profile = response.json()
            self.user_id = profile['id']
            print(f"✅ Profile retrieved: {profile['full_name']} ({profile['role']})")
        else:
            print(f"❌ Profile retrieval failed: {response.status_code}")
            return False
        
        # Update profile
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = self.session.put(f"{BASE_URL}/api/users/profile", json=update_data)
        if response.status_code == 200:
            print("✅ Profile update successful")
        else:
            print(f"❌ Profile update failed: {response.status_code}")
        
        return True
    
    def test_dashboard(self):
        """Test dashboard functionality."""
        print("\n📊 Testing Dashboard...")
        
        # Get dashboard stats
        response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Dashboard stats: {stats}")
        else:
            print(f"❌ Dashboard stats failed: {response.status_code}")
            return False
        
        # Get dashboard charts
        response = self.session.get(f"{BASE_URL}/api/dashboard/charts")
        if response.status_code == 200:
            print("✅ Dashboard charts retrieved")
        else:
            print(f"❌ Dashboard charts failed: {response.status_code}")
        
        return True
    
    def test_forms(self):
        """Test form builder functionality."""
        print("\n📝 Testing Form Builder...")
        
        # Create a form
        form_data = {
            "title": "Test Form",
            "description": "A test form for MVP testing",
            "schema": {
                "fields": [
                    {"name": "name", "type": "text", "label": "Full Name", "required": True},
                    {"name": "email", "type": "email", "label": "Email Address", "required": True},
                    {"name": "message", "type": "textarea", "label": "Message", "required": False}
                ]
            },
            "is_public": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/forms/", json=form_data)
        if response.status_code == 201:
            form_id = response.json()['id']
            print(f"✅ Form created with ID: {form_id}")
        else:
            print(f"❌ Form creation failed: {response.status_code}")
            print(response.text)
            return False
        
        # Get forms list
        response = self.session.get(f"{BASE_URL}/api/forms/")
        if response.status_code == 200:
            forms = response.json()
            print(f"✅ Forms list retrieved: {len(forms['forms'])} forms")
        else:
            print(f"❌ Forms list failed: {response.status_code}")
        
        return True
    
    def test_reports(self):
        """Test report functionality."""
        print("\n📄 Testing Reports...")
        
        # Get reports list
        response = self.session.get(f"{BASE_URL}/api/reports")
        if response.status_code == 200:
            reports = response.json()
            print(f"✅ Reports list retrieved: {len(reports['reports'])} reports")
        else:
            print(f"❌ Reports list failed: {response.status_code}")
            return False
        
        # Get report stats
        response = self.session.get(f"{BASE_URL}/api/reports/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Report stats: {stats}")
        else:
            print(f"❌ Report stats failed: {response.status_code}")
        
        return True
    
    def test_files(self):
        """Test file management."""
        print("\n📁 Testing File Management...")
        
        # Get files list
        response = self.session.get(f"{BASE_URL}/api/files/")
        if response.status_code == 200:
            files = response.json()
            print(f"✅ Files list retrieved: {len(files['files'])} files")
        else:
            print(f"❌ Files list failed: {response.status_code}")
            return False
        
        # Get file stats
        response = self.session.get(f"{BASE_URL}/api/files/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ File stats: {stats}")
        else:
            print(f"❌ File stats failed: {response.status_code}")
        
        return True
    
    def run_all_tests(self):
        """Run all MVP tests."""
        print("🚀 Starting MVP Feature Tests")
        print("=" * 50)
        
        # Test basic connectivity
        try:
            response = self.session.get(f"{BASE_URL}/test-db")
            if response.status_code == 200:
                print("✅ Database connection working")
            else:
                print("❌ Database connection failed")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Flask app. Make sure it's running on localhost:5000")
            return False
        
        # Run individual tests
        tests = [
            self.test_auth,
            self.test_user_profile,
            self.test_dashboard,
            self.test_forms,
            self.test_reports,
            self.test_files
        ]
        
        passed = 0
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"🎯 MVP Test Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 All MVP features are working!")
        else:
            print("⚠️  Some features need attention")
        
        return passed == len(tests)

if __name__ == "__main__":
    print("StratoSys MVP Feature Tester")
    print("Make sure your Flask app is running on localhost:5000")
    print()
    
    tester = MVPTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
