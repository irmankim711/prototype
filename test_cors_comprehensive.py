#!/usr/bin/env python3
"""
Comprehensive CORS Testing Script
Tests all aspects of CORS configuration between frontend and backend
"""

import requests
import json
from datetime import datetime

class CORSTester:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.test_results = []
        
    def log_test(self, test_name, status, details):
        result = {
            'test': test_name,
            'status': 'PASS' if status else 'FAIL',
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        emoji = "✅" if status else "❌"
        print(f"{emoji} {test_name}: {result['status']}")
        if details:
            print(f"   {details}")
        print()
            
    def test_preflight_request(self):
        """Test CORS preflight (OPTIONS) request"""
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = requests.options(
                f"{self.backend_url}/api/analytics/performance-comparison",
                headers=headers
            )
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            success = (
                response.status_code == 200 and
                cors_headers['Access-Control-Allow-Origin'] == 'http://localhost:3000' and
                'GET' in cors_headers['Access-Control-Allow-Methods'] and
                'Authorization' in cors_headers['Access-Control-Allow-Headers']
            )
            
            self.log_test(
                "CORS Preflight Request",
                success,
                f"Status: {response.status_code}, Headers: {cors_headers}"
            )
            
        except Exception as e:
            self.log_test("CORS Preflight Request", False, f"Error: {e}")
            
    def test_actual_request_with_cors(self):
        """Test actual GET request with CORS headers"""
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.backend_url}/api/analytics/performance-comparison",
                headers=headers
            )
            
            # Should get 401 (auth required) not CORS error
            success = response.status_code == 401
            
            self.log_test(
                "Actual Request with CORS",
                success,
                f"Status: {response.status_code} (401 expected for auth)"
            )
            
        except requests.exceptions.ConnectionError:
            self.log_test("Actual Request with CORS", False, "Connection refused - backend not running")
        except Exception as e:
            self.log_test("Actual Request with CORS", False, f"Error: {e}")
            
    def test_multiple_origins(self):
        """Test CORS with different frontend origins"""
        origins = [
            'http://localhost:3000',  # React default
            'http://localhost:3001',  # Alternative React
            'http://localhost:5173',  # Vite default
            'http://localhost:5174'   # Alternative Vite
        ]
        
        for origin in origins:
            try:
                headers = {
                    'Origin': origin,
                    'Access-Control-Request-Method': 'GET'
                }
                
                response = requests.options(
                    f"{self.backend_url}/api/analytics/dashboard/stats",
                    headers=headers
                )
                
                success = (
                    response.status_code == 200 and
                    response.headers.get('Access-Control-Allow-Origin') == origin
                )
                
                self.log_test(
                    f"CORS Origin {origin}",
                    success,
                    f"Status: {response.status_code}, Allowed Origin: {response.headers.get('Access-Control-Allow-Origin')}"
                )
                
            except Exception as e:
                self.log_test(f"CORS Origin {origin}", False, f"Error: {e}")
                
    def test_health_endpoint_cors(self):
        """Test CORS on health endpoint"""
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.backend_url}/health", headers=headers)
            
            success = response.status_code == 200
            
            self.log_test(
                "Health Endpoint CORS",
                success,
                f"Status: {response.status_code}, Response: {response.json().get('status', 'unknown')}"
            )
            
        except Exception as e:
            self.log_test("Health Endpoint CORS", False, f"Error: {e}")
            
    def test_credentials_support(self):
        """Test credentials support in CORS"""
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization'
            }
            
            response = requests.options(
                f"{self.backend_url}/api/analytics/performance-comparison",
                headers=headers
            )
            
            credentials_allowed = response.headers.get('Access-Control-Allow-Credentials') == 'true'
            
            self.log_test(
                "CORS Credentials Support",
                credentials_allowed,
                f"Credentials Allowed: {credentials_allowed}"
            )
            
        except Exception as e:
            self.log_test("CORS Credentials Support", False, f"Error: {e}")
            
    def run_all_tests(self):
        """Run all CORS tests"""
        print("🔍 Comprehensive CORS Testing")
        print("=" * 50)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        print()
        
        self.test_health_endpoint_cors()
        self.test_preflight_request()
        self.test_actual_request_with_cors()
        self.test_multiple_origins()
        self.test_credentials_support()
        
        # Summary
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        total = len(self.test_results)
        
        print("=" * 50)
        print(f"📊 CORS TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All CORS tests PASSED! Frontend-Backend communication should work.")
        else:
            print("⚠️  Some CORS tests failed. Check configuration.")
            
        print("=" * 50)
        
        # Save detailed results
        with open(f"cors_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(self.test_results, f, indent=2)
            
        return passed == total

if __name__ == "__main__":
    tester = CORSTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
