#!/usr/bin/env python3
"""
Comprehensive smoke test for the MVP template system.
Tests all major functionality including template processing, preview generation, and downloads.
"""

import requests
import json
import time
import os
import base64
from typing import Dict, List, Optional

class MVPSmokeTest:
    def __init__(self, base_url: str = "http://localhost:5000/api/mvp"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", response_data: Optional[dict] = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        if response_data:
            result["response"] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_server_connection(self) -> bool:
        """Test if the server is running and responsive"""
        try:
            response = self.session.get(f"{self.base_url}/templates/list")
            if response.status_code == 200:
                self.log_test("Server Connection", True, "Server is running and responsive")
                return True
            else:
                self.log_test("Server Connection", False, f"Server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("Server Connection", False, "Cannot connect to server. Make sure it's running on localhost:5000")
            return False
        except Exception as e:
            self.log_test("Server Connection", False, f"Unexpected error: {str(e)}")
            return False
    
    def test_list_templates(self) -> Optional[List[Dict]]:
        """Test listing available templates"""
        try:
            response = self.session.get(f"{self.base_url}/templates/list")
            if response.status_code == 200:
                templates = response.json()
                if templates:
                    self.log_test("List Templates", True, f"Found {len(templates)} templates", {"templates": templates})
                    return templates
                else:
                    self.log_test("List Templates", False, "No templates found")
                    return None
            else:
                self.log_test("List Templates", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("List Templates", False, f"Error: {str(e)}")
            return None
    
    def test_extract_placeholders(self, template_name: str) -> Optional[List[str]]:
        """Test extracting placeholders from a template"""
        try:
            response = self.session.get(f"{self.base_url}/templates/{template_name}/placeholders")
            if response.status_code == 200:
                data = response.json()
                placeholders = data.get('placeholders', [])
                self.log_test("Extract Placeholders", True, f"Found {len(placeholders)} placeholders", {"placeholders": placeholders})
                return placeholders
            else:
                self.log_test("Extract Placeholders", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Extract Placeholders", False, f"Error: {str(e)}")
            return None
    
    def test_template_preview(self, template_name: str, test_data: Dict) -> bool:
        """Test generating a template preview"""
        try:
            payload = {"data": test_data}
            response = self.session.post(
                f"{self.base_url}/templates/{template_name}/preview",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'preview' in data and data['preview'].startswith('data:application/pdf;base64,'):
                    pdf_size = len(data['preview'])
                    self.log_test("Template Preview", True, f"Generated PDF preview ({pdf_size} chars)", {"filename": data.get('filename')})
                    return True
                else:
                    self.log_test("Template Preview", False, "Invalid preview response format")
                    return False
            else:
                self.log_test("Template Preview", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Template Preview", False, f"Error: {str(e)}")
            return False
    
    def test_generate_report(self, template_name: str, test_data: Dict) -> Optional[str]:
        """Test generating a downloadable report"""
        try:
            payload = {
                "templateFilename": template_name,
                "data": test_data
            }
            response = self.session.post(
                f"{self.base_url}/generate-report",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'downloadUrl' in data and 'filename' in data:
                    self.log_test("Generate Report", True, f"Report generated: {data['filename']}", data)
                    return data['downloadUrl']
                else:
                    self.log_test("Generate Report", False, "Invalid response format")
                    return None
            else:
                self.log_test("Generate Report", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Generate Report", False, f"Error: {str(e)}")
            return None
    
    def test_download_report(self, download_url: str) -> bool:
        """Test downloading a generated report"""
        try:
            full_url = f"http://localhost:5000{download_url}"
            response = self.session.get(full_url)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.content)
                
                if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type or content_length > 1000:
                    self.log_test("Download Report", True, f"Downloaded {content_length} bytes", {"content_type": content_type})
                    return True
                else:
                    self.log_test("Download Report", False, f"Unexpected content type or size: {content_type}, {content_length} bytes")
                    return False
            else:
                self.log_test("Download Report", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Download Report", False, f"Error: {str(e)}")
            return False
    
    def test_download_template(self, template_name: str) -> bool:
        """Test downloading the original template"""
        try:
            response = self.session.get(f"{self.base_url}/templates/{template_name}/download")
            
            if response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get('Content-Type', '')
                
                if content_length > 1000:  # Valid DOCX files should be larger than 1KB
                    self.log_test("Download Template", True, f"Downloaded template {content_length} bytes", {"content_type": content_type})
                    return True
                else:
                    self.log_test("Download Template", False, f"File too small: {content_length} bytes")
                    return False
            else:
                self.log_test("Download Template", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Download Template", False, f"Error: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting MVP Template System Smoke Test")
        print("=" * 50)
        
        # Test 1: Server Connection
        if not self.test_server_connection():
            print("\n❌ Cannot proceed - server is not running")
            return self.generate_report()
        
        # Test 2: List Templates
        templates = self.test_list_templates()
        if not templates:
            print("\n❌ Cannot proceed - no templates available")
            return self.generate_report()
        
        # Use the first template for testing
        test_template = templates[0]['filename']
        print(f"\n📄 Testing with template: {test_template}")
        
        # Test 3: Extract Placeholders
        placeholders = self.test_extract_placeholders(test_template)
        
        # Test 4: Generate test data
        test_data = {}
        if placeholders:
            for placeholder in placeholders[:5]:  # Test with first 5 placeholders
                test_data[placeholder] = f"Test_{placeholder}_Value"
        else:
            # Fallback test data for common placeholders
            test_data = {
                "name": "John Doe",
                "date": "2025-07-26",
                "company": "Test Company",
                "title": "Test Report",
                "description": "This is a test document"
            }
        
        print(f"📝 Using test data: {json.dumps(test_data, indent=2)}")
        
        # Test 5: Template Preview
        self.test_template_preview(test_template, test_data)
        
        # Test 6: Generate Report
        download_url = self.test_generate_report(test_template, test_data)
        
        # Test 7: Download Generated Report
        if download_url:
            self.test_download_report(download_url)
        
        # Test 8: Download Original Template
        self.test_download_template(test_template)
        
        # Generate final report
        return self.generate_report()
    
    def generate_report(self):
        """Generate a summary report of all tests"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 50)
        
        # Save detailed results to file
        with open('smoke_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"💾 Detailed results saved to: smoke_test_results.json")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    print("MVP Template System - Comprehensive Smoke Test")
    print("Make sure the backend server is running on localhost:5000")
    print()
    
    tester = MVPSmokeTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! The system is working correctly.")
        exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the results above.")
        exit(1)
