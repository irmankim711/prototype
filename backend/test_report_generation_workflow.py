#!/usr/bin/env python3
"""
Test Report Generation Workflow
Tests the complete report generation pipeline after database schema fixes
"""

import sys
sys.path.append('.')

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpass123"
}

class ReportGenerationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        
    def test_health_endpoints(self):
        """Test health endpoints"""
        print("🏥 Testing Health Endpoints...")
        
        # Test reports health
        try:
            response = requests.get(f"{self.base_url}/api/reports/health")
            if response.status_code == 200:
                print(f"✅ Reports API Health: {response.json()}")
            else:
                print(f"❌ Reports API Health failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Reports health check failed: {e}")
            return False
        
        return True
    
    def create_test_user(self):
        """Create test user for authentication"""
        print("👤 Creating test user...")
        
        try:
            # Try to register a test user
            response = requests.post(f"{self.base_url}/api/auth/register", json=TEST_USER)
            
            if response.status_code == 201:
                print("✅ Test user created successfully")
                return True
            elif response.status_code == 409:
                print("ℹ️ Test user already exists")
                return True
            else:
                print(f"❌ User creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ User creation error: {e}")
            return False
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            })
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    print("✅ Authentication successful")
                    return True
                else:
                    print(f"❌ No access token in response: {data}")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_protected_endpoints(self):
        """Test that protected endpoints work with authentication"""
        print("🔒 Testing protected endpoints...")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test reports list
        try:
            response = requests.get(f"{self.base_url}/api/reports/", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Reports list: {len(data.get('reports', []))} reports found")
                return True
            else:
                print(f"❌ Reports list failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Protected endpoint test failed: {e}")
            return False
    
    def test_report_generation(self):
        """Test basic report generation"""
        print("📊 Testing report generation...")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create test report data
        report_data = {
            "title": f"Test Report {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Automated test report",
            "data": {
                "test_data": [
                    {"name": "Item 1", "value": 100},
                    {"name": "Item 2", "value": 200},
                    {"name": "Item 3", "value": 150}
                ]
            },
            "config": {
                "template_used": "default",
                "format": "pdf",
                "include_charts": True
            }
        }
        
        try:
            print("📤 Sending report generation request...")
            response = requests.post(f"{self.base_url}/api/reports/generate", 
                                   headers=headers, 
                                   json=report_data)
            
            if response.status_code == 202:
                data = response.json()
                print(f"✅ Report generation started: {data}")
                
                report_id = data.get('report_id')
                if report_id:
                    return self.check_report_status(report_id, headers)
                else:
                    print("❌ No report_id returned")
                    return False
                    
            else:
                print(f"❌ Report generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Report generation error: {e}")
            return False
    
    def check_report_status(self, report_id, headers, max_wait=30):
        """Check report generation status"""
        print(f"⏳ Checking report status for ID: {report_id}")
        
        for i in range(max_wait):
            try:
                response = requests.get(f"{self.base_url}/api/reports/{report_id}/status", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    report = data.get('report', {})
                    status = report.get('status', 'unknown')
                    
                    print(f"📈 Report status: {status}")
                    
                    if status == 'completed':
                        print("✅ Report generation completed!")
                        return True
                    elif status == 'failed':
                        error = report.get('error_message', 'Unknown error')
                        print(f"❌ Report generation failed: {error}")
                        return False
                    elif status in ['pending', 'processing']:
                        print(f"⏳ Still processing... ({i+1}/{max_wait})")
                        time.sleep(1)
                    else:
                        print(f"❓ Unknown status: {status}")
                        time.sleep(1)
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Status check error: {e}")
                time.sleep(1)
        
        print("⏰ Report generation timeout")
        return False
    
    def run_full_test(self):
        """Run complete test suite"""
        print("🚀 Starting Report Generation Test Suite")
        print("=" * 60)
        
        tests = [
            ("Health Endpoints", self.test_health_endpoints),
            ("User Creation", self.create_test_user),
            ("Authentication", self.authenticate), 
            ("Protected Endpoints", self.test_protected_endpoints),
            ("Report Generation", self.test_report_generation)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}...")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    print(f"✅ {test_name} passed")
                else:
                    print(f"❌ {test_name} failed")
            except Exception as e:
                print(f"💥 {test_name} crashed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY:")
        print("=" * 60)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Report generation system is working!")
        else:
            print(f"⚠️ {total - passed} tests failed. System needs attention.")
        
        return passed == total

if __name__ == "__main__":
    tester = ReportGenerationTester()
    success = tester.run_full_test()
    sys.exit(0 if success else 1)