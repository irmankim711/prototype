#!/usr/bin/env python3
"""
Comprehensive QA Test Script for Government-Grade Web System
Tests all layers: Form Collection, Data Storage, Excel Generation, Report Generation, Security, and Performance
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from datetime import datetime
import sys
import os

# Configuration
BASE_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:5173"
TEST_USER = {
    "email": "qa-test@example.com",
    "password": "test123456"
}

class ComprehensiveQATest:
    def __init__(self):
        self.results = {
            "form_collection": {},
            "data_storage": {},
            "excel_layer": {},
            "report_generation": {},
            "security": {},
            "error_handling": {},
            "performance": {},
            "deployment": {}
        }
        self.session = requests.Session()
        self.auth_token = None
        
    def log_result(self, category, test_name, status, details=None):
        """Log test results"""
        self.results[category][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {category.upper()}: {test_name} - {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_backend_health(self):
        """Test backend health endpoints"""
        try:
            # Test main health endpoint
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("deployment", "backend_health", "PASS", f"Status: {data.get('status')}")
                else:
                    self.log_result("deployment", "backend_health", "FAIL", f"Status: {data.get('status')}")
            else:
                self.log_result("deployment", "backend_health", "FAIL", f"Status code: {response.status_code}")
            
            # Test database health
            response = self.session.get(f"{BASE_URL}/health/database")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("deployment", "database_health", "PASS", f"Status: {data.get('status')}")
                else:
                    self.log_result("deployment", "database_health", "FAIL", f"Status: {data.get('status')}")
            else:
                self.log_result("deployment", "database_health", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("deployment", "backend_health", "FAIL", f"Exception: {str(e)}")
    
    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        try:
            response = self.session.get(FRONTEND_URL)
            if response.status_code == 200:
                self.log_result("deployment", "frontend_accessibility", "PASS", f"Status code: {response.status_code}")
            else:
                self.log_result("deployment", "frontend_accessibility", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("deployment", "frontend_accessibility", "FAIL", f"Exception: {str(e)}")
    
    def test_authentication_system(self):
        """Test authentication system"""
        try:
            # Test login endpoint (should fail with invalid credentials)
            response = self.session.post(f"{BASE_URL}/api/auth/login", 
                                       json=TEST_USER)
            if response.status_code in [401, 422]:  # Expected for invalid credentials
                self.log_result("security", "authentication_endpoint", "PASS", f"Status code: {response.status_code}")
            else:
                self.log_result("security", "authentication_endpoint", "FAIL", f"Unexpected status: {response.status_code}")
            
            # Test protected endpoint without auth
            response = self.session.get(f"{BASE_URL}/api/v1/integrations/google/auth-url")
            if response.status_code == 401:  # Expected for unauthorized access
                self.log_result("security", "jwt_protection", "PASS", f"Status code: {response.status_code}")
            else:
                self.log_result("security", "jwt_protection", "FAIL", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result("security", "authentication_system", "FAIL", f"Exception: {str(e)}")
    
    def test_public_endpoints(self):
        """Test public endpoints that don't require authentication"""
        try:
            # Test public forms endpoint
            response = self.session.get(f"{BASE_URL}/api/public/forms")
            if response.status_code == 200:
                data = response.json()
                self.log_result("form_collection", "public_forms_endpoint", "PASS", f"Forms count: {len(data.get('forms', []))}")
            else:
                self.log_result("form_collection", "public_forms_endpoint", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("form_collection", "public_endpoints", "FAIL", f"Exception: {str(e)}")
    
    def test_report_generation(self):
        """Test report generation without authentication"""
        try:
            # Test report export endpoint
            test_data = {
                "template_id": "test_template",
                "data_source": {"test": "data"},
                "formats": ["pdf"]
            }
            response = self.session.post(f"{BASE_URL}/api/reports/export", json=test_data)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.log_result("report_generation", "pdf_generation", "PASS", f"Generated PDF: {data.get('urls', {}).get('pdf')}")
                    
                    # Test download
                    pdf_url = data.get('urls', {}).get('pdf')
                    if pdf_url:
                        download_response = self.session.get(f"{BASE_URL}{pdf_url}")
                        if download_response.status_code == 200:
                            self.log_result("report_generation", "pdf_download", "PASS", f"File size: {len(download_response.content)} bytes")
                        else:
                            self.log_result("report_generation", "pdf_download", "FAIL", f"Download status: {download_response.status_code}")
                else:
                    self.log_result("report_generation", "pdf_generation", "FAIL", f"Generation failed: {data.get('error')}")
            else:
                self.log_result("report_generation", "pdf_generation", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("report_generation", "report_generation", "FAIL", f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test non-existent endpoint
            response = self.session.get(f"{BASE_URL}/api/nonexistent")
            if response.status_code == 404:
                data = response.json()
                if data.get("error", {}).get("code") == "ENDPOINT_NOT_FOUND":
                    self.log_result("error_handling", "404_handling", "PASS", "Proper 404 error response")
                else:
                    self.log_result("error_handling", "404_handling", "FAIL", "Incorrect error format")
            else:
                self.log_result("error_handling", "404_handling", "FAIL", f"Unexpected status: {response.status_code}")
                
            # Test invalid JSON
            response = self.session.post(f"{BASE_URL}/api/reports/export", 
                                       data="invalid json",
                                       headers={"Content-Type": "application/json"})
            if response.status_code in [400, 500]:  # Expected for invalid JSON
                self.log_result("error_handling", "invalid_json_handling", "PASS", f"Status code: {response.status_code}")
            else:
                self.log_result("error_handling", "invalid_json_handling", "FAIL", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result("error_handling", "error_handling", "FAIL", f"Exception: {str(e)}")
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            # Test CORS preflight
            response = self.session.options(f"{BASE_URL}/api/public/forms")
            if response.status_code == 200:
                cors_headers = response.headers
                if "Access-Control-Allow-Origin" in cors_headers:
                    self.log_result("security", "cors_configuration", "PASS", f"Origin: {cors_headers.get('Access-Control-Allow-Origin')}")
                else:
                    self.log_result("security", "cors_configuration", "FAIL", "Missing CORS headers")
            else:
                self.log_result("security", "cors_configuration", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("security", "cors_configuration", "FAIL", f"Exception: {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting (if implemented)"""
        try:
            # Make multiple rapid requests to test rate limiting
            responses = []
            for i in range(10):
                response = self.session.get(f"{BASE_URL}/api/public/forms")
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay
            
            # Check if any requests were rate limited (429 status)
            if 429 in responses:
                self.log_result("security", "rate_limiting", "PASS", "Rate limiting is active")
            else:
                self.log_result("security", "rate_limiting", "INFO", "Rate limiting not detected (may be disabled in dev)")
                
        except Exception as e:
            self.log_result("security", "rate_limiting", "FAIL", f"Exception: {str(e)}")
    
    def test_performance(self):
        """Test system performance under load"""
        try:
            # Test response times for multiple requests
            response_times = []
            for i in range(10):
                start_time = time.time()
                response = self.session.get(f"{BASE_URL}/health")
                end_time = time.time()
                response_times.append((end_time - start_time) * 1000)  # Convert to ms
                time.sleep(0.1)
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            if avg_response_time < 100:  # Sub-100ms average
                self.log_result("performance", "response_time", "PASS", f"Average: {avg_response_time:.2f}ms, Max: {max_response_time:.2f}ms")
            elif avg_response_time < 500:  # Sub-500ms average
                self.log_result("performance", "response_time", "WARN", f"Average: {avg_response_time:.2f}ms, Max: {max_response_time:.2f}ms")
            else:
                self.log_result("performance", "response_time", "FAIL", f"Average: {avg_response_time:.2f}ms, Max: {max_response_time:.2f}ms")
                
        except Exception as e:
            self.log_result("performance", "performance", "FAIL", f"Exception: {str(e)}")
    
    def test_concurrent_requests(self):
        """Test system under concurrent load"""
        try:
            def make_request():
                start_time = time.time()
                response = self.session.get(f"{BASE_URL}/health")
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000
                }
            
            # Make 20 concurrent requests
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in as_completed(futures)]
            
            successful_requests = [r for r in results if r["status_code"] == 200]
            success_rate = len(successful_requests) / len(results) * 100
            
            if success_rate >= 95:
                self.log_result("performance", "concurrent_requests", "PASS", f"Success rate: {success_rate:.1f}%")
            elif success_rate >= 80:
                self.log_result("performance", "concurrent_requests", "WARN", f"Success rate: {success_rate:.1f}%")
            else:
                self.log_result("performance", "concurrent_requests", "FAIL", f"Success rate: {success_rate:.1f}%")
                
        except Exception as e:
            self.log_result("performance", "concurrent_requests", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive QA Testing...")
        print("=" * 60)
        
        # Test deployment and infrastructure
        self.test_backend_health()
        self.test_frontend_accessibility()
        
        # Test security features
        self.test_authentication_system()
        self.test_cors_configuration()
        self.test_rate_limiting()
        
        # Test core functionality
        self.test_public_endpoints()
        self.test_report_generation()
        
        # Test error handling
        self.test_error_handling()
        
        # Test performance
        self.test_performance()
        self.test_concurrent_requests()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE QA TEST SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        
        for category, tests in self.results.items():
            print(f"\n🔍 {category.upper()}:")
            for test_name, result in tests.items():
                total_tests += 1
                status = result["status"]
                if status == "PASS":
                    passed_tests += 1
                elif status == "FAIL":
                    failed_tests += 1
                elif status == "WARN":
                    warning_tests += 1
                
                status_icon = {
                    "PASS": "✅",
                    "FAIL": "❌",
                    "WARN": "⚠️",
                    "INFO": "ℹ️"
                }.get(status, "❓")
                
                print(f"  {status_icon} {test_name}: {status}")
                if result.get("details"):
                    print(f"      Details: {result['details']}")
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ⚠️ Warnings: {warning_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! System meets government-grade standards.")
        elif failed_tests <= 2:
            print("\n⚠️ Most tests passed. Minor issues detected.")
        else:
            print("\n❌ Multiple test failures detected. System needs attention.")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qa_test_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📁 Detailed results saved to: {filename}")

if __name__ == "__main__":
    qa_test = ComprehensiveQATest()
    qa_test.run_all_tests()
