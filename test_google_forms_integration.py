"""
Test Google Forms Integration
Tests the complete workflow from authentication to automated report generation
"""

import requests
import json
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.google_forms_service import google_forms_service
from app.services.automated_report_system import automated_report_system

class GoogleFormsIntegrationTest:
    """Test class for Google Forms integration functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000/api"
        self.token = None
        self.test_results = []
    
    def log_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
    
    def test_google_forms_service_methods(self):
        """Test Google Forms service methods directly"""
        print("\n🔍 Testing Google Forms Service Methods...")
        
        # Test user ID (mock)
        test_user_id = "test_user_123"
        
        try:
            # Test get_authorization_url
            auth_url = google_forms_service.get_authorization_url(test_user_id)
            if auth_url and "accounts.google.com" in auth_url:
                self.log_result(
                    "get_authorization_url", 
                    True, 
                    "Authorization URL generated successfully"
                )
            else:
                self.log_result(
                    "get_authorization_url", 
                    False, 
                    "Failed to generate authorization URL"
                )
        except Exception as e:
            self.log_result(
                "get_authorization_url", 
                False, 
                f"Exception: {str(e)}"
            )
        
        try:
            # Test get_credentials (will return None without valid auth)
            credentials = google_forms_service.get_credentials(test_user_id)
            self.log_result(
                "get_credentials", 
                True, 
                f"Credentials check completed (None expected): {credentials is None}"
            )
        except Exception as e:
            self.log_result(
                "get_credentials", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def test_automated_report_system_methods(self):
        """Test automated report system methods"""
        print("\n📊 Testing Automated Report System...")
        
        try:
            # Test Google Forms automated report generation (will use mock data)
            test_form_id = "test_form_12345"
            test_user_id = 1
            test_config = {
                'format': 'pdf',
                'include_charts': True,
                'include_ai_analysis': True
            }
            
            # This should work with mock data fallback
            result = automated_report_system.generate_google_forms_automated_report(
                test_form_id, test_config, test_user_id
            )
            
            if result.get('success'):
                self.log_result(
                    "generate_google_forms_automated_report", 
                    True, 
                    f"Report generated successfully: {result.get('summary', {})}"
                )
            else:
                self.log_result(
                    "generate_google_forms_automated_report", 
                    False, 
                    f"Report generation failed: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            self.log_result(
                "generate_google_forms_automated_report", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def test_google_forms_routes(self):
        """Test Google Forms API routes (requires running server)"""
        print("\n🌐 Testing Google Forms Routes...")
        
        # These tests require a running server and authentication
        routes_to_test = [
            ('/google-forms/status', 'GET'),
            ('/google-forms/forms', 'GET'),
            ('/google-forms/oauth/authorize', 'POST')
        ]
        
        for route, method in routes_to_test:
            try:
                url = f"{self.base_url}{route}"
                
                if method == 'GET':
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, json={}, timeout=5)
                
                # Even without auth, we should get a proper error response
                if response.status_code in [401, 422]:  # JWT required
                    self.log_result(
                        f"route_{route.replace('/', '_')}", 
                        True, 
                        f"Route accessible, requires auth (status: {response.status_code})"
                    )
                else:
                    self.log_result(
                        f"route_{route.replace('/', '_')}", 
                        False, 
                        f"Unexpected status: {response.status_code}"
                    )
                    
            except requests.exceptions.ConnectionError:
                self.log_result(
                    f"route_{route.replace('/', '_')}", 
                    False, 
                    "Server not running - cannot test routes"
                )
            except Exception as e:
                self.log_result(
                    f"route_{route.replace('/', '_')}", 
                    False, 
                    f"Exception: {str(e)}"
                )
    
    def test_mock_data_generation(self):
        """Test mock data generation for development"""
        print("\n🎭 Testing Mock Data Generation...")
        
        try:
            # Test mock responses generation
            mock_data = google_forms_service._generate_mock_responses_for_report(
                "test_form_id", "last_30_days"
            )
            
            if mock_data and 'responses' in mock_data:
                response_count = len(mock_data['responses'])
                self.log_result(
                    "mock_data_generation", 
                    True, 
                    f"Generated {response_count} mock responses"
                )
                
                # Test analysis generation
                if 'analysis' in mock_data:
                    analysis = mock_data['analysis']
                    insights_count = len(analysis.get('question_insights', []))
                    self.log_result(
                        "mock_analysis_generation", 
                        True, 
                        f"Generated analysis with {insights_count} question insights"
                    )
                else:
                    self.log_result(
                        "mock_analysis_generation", 
                        False, 
                        "No analysis data in mock response"
                    )
            else:
                self.log_result(
                    "mock_data_generation", 
                    False, 
                    "Mock data generation failed"
                )
                
        except Exception as e:
            self.log_result(
                "mock_data_generation", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def test_data_processing_methods(self):
        """Test data processing and analysis methods"""
        print("\n🔬 Testing Data Processing Methods...")
        
        try:
            # Create sample response data
            sample_responses = [
                {
                    'responseId': 'resp1',
                    'createTime': '2024-01-15T10:30:00Z',
                    'answers': {
                        'q1': {'textAnswers': {'answers': [{'value': 'Test Answer 1'}]}},
                        'q2': {'textAnswers': {'answers': [{'value': 'Test Answer 2'}]}}
                    }
                },
                {
                    'responseId': 'resp2',
                    'createTime': '2024-01-16T14:20:00Z',
                    'answers': {
                        'q1': {'textAnswers': {'answers': [{'value': 'Test Answer 3'}]}},
                        'q2': {'textAnswers': {'answers': [{'value': 'Test Answer 4'}]}}
                    }
                }
            ]
            
            # Create sample form structure
            sample_form_structure = {
                'questions': {
                    'q1': {'title': 'Question 1', 'type': 'text'},
                    'q2': {'title': 'Question 2', 'type': 'text'}
                }
            }
            
            # Test comprehensive analysis
            analysis = google_forms_service._generate_comprehensive_analysis(
                sample_responses, sample_form_structure
            )
            
            if analysis and 'response_patterns' in analysis:
                self.log_result(
                    "comprehensive_analysis", 
                    True, 
                    f"Analysis generated with patterns, completion stats, etc."
                )
            else:
                self.log_result(
                    "comprehensive_analysis", 
                    False, 
                    "Comprehensive analysis failed"
                )
                
        except Exception as e:
            self.log_result(
                "comprehensive_analysis", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting Google Forms Integration Tests")
        print("=" * 50)
        
        # Run test suites
        self.test_google_forms_service_methods()
        self.test_automated_report_system_methods()
        self.test_mock_data_generation()
        self.test_data_processing_methods()
        self.test_google_forms_routes()
        
        # Generate summary
        print("\n" + "=" * 50)
        print("📋 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save detailed results
        results_file = f"google_forms_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return passed_tests, failed_tests

def main():
    """Main test execution"""
    tester = GoogleFormsIntegrationTest()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
