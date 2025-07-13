#!/usr/bin/env python3
"""
Complete MVP API Test Suite
Tests all implemented endpoints to ensure they're working correctly.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

class StratoSysMVPTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        
    def print_separator(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        self.print_separator("🔐 Testing Authentication Endpoints")
        
        # Test login with existing user
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print("✅ Login successful")
                
                # Test /auth/me endpoint
                me_response = self.session.get(f"{BASE_URL}/auth/me")
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    self.user_id = user_data['id']
                    print(f"✅ User info retrieved: {user_data['email']}")
                else:
                    print(f"❌ /auth/me failed: {me_response.status_code}")
                    
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Auth test failed: {e}")
            return False
            
        return True
    
    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        self.print_separator("📊 Testing Dashboard Endpoints")
        
        endpoints = [
            '/api/dashboard/stats',
            '/api/dashboard/charts',
            '/api/dashboard/recent',
            '/api/dashboard/summary',
            '/api/dashboard/performance',
            '/api/dashboard/timeline'
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                    results.append(True)
                else:
                    print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
                    results.append(False)
            except Exception as e:
                print(f"❌ {endpoint}: Exception - {e}")
                results.append(False)
        
        # Test dashboard refresh (POST)
        try:
            response = self.session.post(f"{BASE_URL}/api/dashboard/refresh")
            if response.status_code == 200:
                print("✅ /api/dashboard/refresh: OK")
                results.append(True)
            else:
                print(f"❌ /api/dashboard/refresh: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ /api/dashboard/refresh: Exception - {e}")
            results.append(False)
            
        return all(results)
    
    def test_user_endpoints(self):
        """Test user management endpoints"""
        self.print_separator("👤 Testing User Management Endpoints")
        
        results = []
        
        # Test get profile
        try:
            response = self.session.get(f"{BASE_URL}/api/users/profile")
            if response.status_code == 200:
                print("✅ /api/users/profile: OK")
                results.append(True)
            else:
                print(f"❌ /api/users/profile: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ /api/users/profile: Exception - {e}")
            results.append(False)
        
        # Test get settings
        try:
            response = self.session.get(f"{BASE_URL}/api/users/settings")
            if response.status_code == 200:
                print("✅ /api/users/settings: OK")
                results.append(True)
            else:
                print(f"❌ /api/users/settings: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ /api/users/settings: Exception - {e}")
            results.append(False)
            
        return all(results)
    
    def test_report_endpoints(self):
        """Test report endpoints"""
        self.print_separator("📄 Testing Report Endpoints")
        
        endpoints = [
            '/api/reports',
            '/api/reports/recent',
            '/api/reports/stats',
            '/api/reports/templates'
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                    results.append(True)
                else:
                    print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
                    results.append(False)
            except Exception as e:
                print(f"❌ {endpoint}: Exception - {e}")
                results.append(False)
                
        return all(results)
    
    def test_form_endpoints(self):
        """Test form endpoints"""
        self.print_separator("📝 Testing Form Endpoints")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/forms/")
            if response.status_code == 200:
                print("✅ /api/forms/: OK")
                return True
            else:
                print(f"❌ /api/forms/: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ /api/forms/: Exception - {e}")
            return False
    
    def test_file_endpoints(self):
        """Test file endpoints"""
        self.print_separator("📁 Testing File Endpoints")
        
        endpoints = [
            '/api/files/',
            '/api/files/stats'
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                    results.append(True)
                else:
                    print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
                    results.append(False)
            except Exception as e:
                print(f"❌ {endpoint}: Exception - {e}")
                results.append(False)
                
        return all(results)
    
    def test_database_connection(self):
        """Test database connectivity"""
        self.print_separator("🗄️ Testing Database Connection")
        
        try:
            response = self.session.get(f"{BASE_URL}/test-db")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Database connection successful")
                print(f"   Tables found: {data.get('table_count', 0)}")
                return True
            else:
                print(f"❌ Database test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Database test exception: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        self.print_separator("🚀 StratoSys MVP - Comprehensive API Test Suite")
        
        print("Testing server connectivity...")
        try:
            response = requests.get(f"{BASE_URL}/test-db", timeout=5)
            print(f"✅ Server is responsive")
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            return False
        
        # Run all test suites
        test_results = {
            "Database": self.test_database_connection(),
            "Authentication": self.test_auth_endpoints(),
            "Dashboard": self.test_dashboard_endpoints(),
            "Users": self.test_user_endpoints(),
            "Reports": self.test_report_endpoints(),
            "Forms": self.test_form_endpoints(),
            "Files": self.test_file_endpoints()
        }
        
        # Summary
        self.print_separator("📋 Test Results Summary")
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:15} {status}")
            if result:
                passed += 1
        
        print(f"\nOverall Result: {passed}/{total} test suites passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Your MVP backend is fully functional!")
            print("✨ Ready to connect to frontend!")
        else:
            print(f"\n⚠️  Some tests failed. Please check the issues above.")
            
        return passed == total

if __name__ == "__main__":
    tester = StratoSysMVPTester()
    success = tester.run_comprehensive_test()
    
    print(f"\n{'='*60}")
    if success:
        print("🎯 MVP Backend Status: READY FOR FRONTEND INTEGRATION")
    else:
        print("🔧 MVP Backend Status: NEEDS FIXES")
    print(f"{'='*60}")
