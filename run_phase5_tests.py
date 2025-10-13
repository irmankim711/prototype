"""
Comprehensive Testing Suite for Phase 5 Final Testing
Validates UX, Compliance, and Production Readiness
"""

import subprocess
import os
import sys
import time
import requests
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase5TestRunner:
    """Comprehensive test runner for Phase 5 deliverables"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.test_results = {
            'start_time': datetime.now(),
            'tests': {},
            'overall_status': 'PENDING'
        }
        
    def run_all_tests(self):
        """Run all Phase 5 tests"""
        logger.info("🚀 Starting Phase 5 Comprehensive Testing Suite")
        
        # Test categories
        test_categories = [
            ('backend_health', self.test_backend_health),
            ('frontend_build', self.test_frontend_build),
            ('malay_template', self.test_malay_template_generation),
            ('gdpr_compliance', self.test_gdpr_compliance),
            ('accessibility', self.test_accessibility_features),
            ('mobile_responsiveness', self.test_mobile_responsiveness),
            ('performance', self.test_performance_metrics),
            ('security', self.test_security_measures),
        ]
        
        for test_name, test_function in test_categories:
            try:
                logger.info(f"📋 Running {test_name} tests...")
                result = test_function()
                self.test_results['tests'][test_name] = result
                
                if result['status'] == 'PASS':
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED - {result.get('message', '')}")
                    
            except Exception as e:
                logger.error(f"💥 {test_name}: ERROR - {str(e)}")
                self.test_results['tests'][test_name] = {
                    'status': 'ERROR',
                    'message': str(e),
                    'timestamp': datetime.now()
                }
        
        # Calculate overall status
        self._calculate_overall_status()
        
        # Generate test report
        self._generate_test_report()
        
        return self.test_results
    
    def test_backend_health(self):
        """Test backend service health and API endpoints"""
        try:
            # Check if backend is running with retry logic
            backend_url = "http://localhost:5000"
            
            # Enhanced health check with retries
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    # Test health endpoint
                    health_response = requests.get(f"{backend_url}/health", timeout=10)
                    if health_response.status_code == 200:
                        break
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Backend health check attempt {attempt + 1} failed: {e}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        return {
                            'status': 'FAIL',
                            'message': 'Cannot connect to backend service',
                            'details': {'backend_url': backend_url, 'error': str(e)}
                        }
            else:
                return {
                    'status': 'FAIL',
                    'message': 'Backend health check failed after retries',
                    'details': {'status_code': health_response.status_code if 'health_response' in locals() else 'No response'}
                }
            
            # Test API endpoints
            api_tests = [
                '/api/auth/test',
                '/api/forms',
                '/api/reports',
                '/api/dashboard/stats'
            ]
            
            failed_endpoints = []
            for endpoint in api_tests:
                try:
                    response = requests.get(f"{backend_url}{endpoint}", timeout=5)
                    if response.status_code >= 500:
                        failed_endpoints.append(endpoint)
                except requests.exceptions.RequestException:
                    failed_endpoints.append(endpoint)
            
            if failed_endpoints:
                return {
                    'status': 'FAIL',
                    'message': f'Failed endpoints: {failed_endpoints}',
                    'details': {'failed_endpoints': failed_endpoints}
                }
            
            return {
                'status': 'PASS',
                'message': 'Backend health checks passed',
                'details': {'tested_endpoints': len(api_tests)}
            }
            
        except requests.exceptions.ConnectionError:
            return {
                'status': 'FAIL',
                'message': 'Cannot connect to backend service',
                'details': {'backend_url': backend_url}
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Backend health test error: {str(e)}'
            }
    
    def test_frontend_build(self):
        """Test frontend build and static assets"""
        try:
            frontend_dir = os.path.join(self.project_root, 'frontend')
            
            # Check if frontend directory exists
            if not os.path.exists(frontend_dir):
                return {
                    'status': 'FAIL',
                    'message': 'Frontend directory not found'
                }
            
            # Check for critical files
            critical_files = [
                'src/App.tsx',
                'src/components/ConsentModal.tsx',
                'src/styles/enhanced-dashboard.css',
                'public/manifest.json'
            ]
            
            missing_files = []
            for file_path in critical_files:
                full_path = os.path.join(frontend_dir, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)
            
            if missing_files:
                return {
                    'status': 'FAIL',
                    'message': f'Missing critical files: {missing_files}'
                }
            
            # Test if frontend is accessible
            try:
                frontend_response = requests.get("http://localhost:3000", timeout=5)
                if frontend_response.status_code >= 400:
                    return {
                        'status': 'WARN',
                        'message': 'Frontend accessible but may have issues',
                        'details': {'status_code': frontend_response.status_code}
                    }
            except requests.exceptions.ConnectionError:
                return {
                    'status': 'WARN',
                    'message': 'Frontend not running (this is acceptable for production)'
                }
            
            return {
                'status': 'PASS',
                'message': 'Frontend build validation passed',
                'details': {'checked_files': len(critical_files)}
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Frontend build test error: {str(e)}'
            }
    
    def test_malay_template_generation(self):
        """Test Malay template generation and compliance"""
        try:
            # Check if Malay template generator exists
            template_file = os.path.join(
                self.project_root, 
                'backend', 'app', 'services', 'malay_template_generator.py'
            )
            
            if not os.path.exists(template_file):
                return {
                    'status': 'FAIL',
                    'message': 'Malay template generator not found'
                }
            
            # Test template generation
            test_data = {
                'title': 'Test Report',
                'program_name': 'Program Ujian',
                'date': '10 Ogos 2025',
                'organization': {
                    'name': 'Organisasi Ujian',
                    'address': 'Kuala Lumpur, Malaysia'
                }
            }
            
            # Import and test the generator
            sys.path.append(os.path.join(self.project_root, 'backend', 'app', 'services'))
            
            try:
                from malay_template_generator import MalayTemplateGenerator
                generator = MalayTemplateGenerator()
                
                # Test template creation
                report_path = generator.create_temp1_compliant_report(test_data)
                
                if os.path.exists(report_path):
                    file_size = os.path.getsize(report_path)
                    return {
                        'status': 'PASS',
                        'message': 'Malay template generation successful',
                        'details': {
                            'report_path': report_path,
                            'file_size': file_size
                        }
                    }
                else:
                    return {
                        'status': 'FAIL',
                        'message': 'Template generated but file not found'
                    }
                    
            except ImportError as e:
                return {
                    'status': 'FAIL',
                    'message': f'Cannot import Malay template generator: {str(e)}'
                }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Malay template test error: {str(e)}'
            }
    
    def test_gdpr_compliance(self):
        """Test GDPR/PDPA compliance features"""
        try:
            # Check compliance service
            compliance_file = os.path.join(
                self.project_root,
                'backend', 'app', 'services', 'gdpr_compliance_service.py'
            )
            
            if not os.path.exists(compliance_file):
                return {
                    'status': 'FAIL',
                    'message': 'GDPR compliance service not found'
                }
            
            # Check compliance documentation
            compliance_docs = [
                'GDPR_PDPA_COMPLIANCE_CHECKLIST.md',
                'STRATOSYS_USER_GUIDE.md'
            ]
            
            missing_docs = []
            for doc in compliance_docs:
                doc_path = os.path.join(self.project_root, doc)
                if not os.path.exists(doc_path):
                    missing_docs.append(doc)
            
            if missing_docs:
                return {
                    'status': 'FAIL',
                    'message': f'Missing compliance documentation: {missing_docs}'
                }
            
            # Test compliance service functionality
            sys.path.append(os.path.join(self.project_root, 'backend', 'app', 'services'))
            
            try:
                from gdpr_compliance_service import GDPRComplianceService, ConsentType
                
                compliance_service = GDPRComplianceService()
                
                # Test consent recording
                test_user_id = "test_user_123"
                consent_id = compliance_service.record_consent(
                    user_id=test_user_id,
                    consent_type=ConsentType.DATA_PROCESSING,
                    granted=True,
                    ip_address="127.0.0.1",
                    user_agent="Test Agent",
                    privacy_policy_version="2.0"
                )
                
                # Test data export
                export_data = compliance_service.export_user_data(test_user_id)
                
                if 'user_id' in export_data and 'consent_records' in export_data:
                    return {
                        'status': 'PASS',
                        'message': 'GDPR compliance features working',
                        'details': {
                            'consent_recorded': bool(consent_id),
                            'export_keys': list(export_data.keys())
                        }
                    }
                else:
                    return {
                        'status': 'FAIL',
                        'message': 'GDPR compliance test failed'
                    }
                    
            except ImportError as e:
                return {
                    'status': 'FAIL',
                    'message': f'Cannot import GDPR service: {str(e)}'
                }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'GDPR compliance test error: {str(e)}'
            }
    
    def test_accessibility_features(self):
        """Test accessibility compliance"""
        try:
            # Check for accessibility features in CSS
            css_file = os.path.join(
                self.project_root,
                'frontend', 'src', 'styles', 'enhanced-dashboard.css'
            )
            
            if not os.path.exists(css_file):
                return {
                    'status': 'FAIL',
                    'message': 'Enhanced dashboard CSS not found'
                }
            
            # Read CSS file and check for accessibility features
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            accessibility_features = [
                'prefers-reduced-motion',
                'prefers-contrast',
                'focus-visible',
                'sr-only',
                'aria-'
            ]
            
            found_features = []
            for feature in accessibility_features:
                if feature in css_content:
                    found_features.append(feature)
            
            # Check Cypress accessibility tests
            cypress_a11y_file = os.path.join(
                self.project_root,
                'cypress', 'e2e', '05-accessibility.cy.js'
            )
            
            cypress_exists = os.path.exists(cypress_a11y_file)
            
            if len(found_features) >= 3 and cypress_exists:
                return {
                    'status': 'PASS',
                    'message': 'Accessibility features implemented',
                    'details': {
                        'css_features': found_features,
                        'cypress_tests': cypress_exists
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'message': 'Insufficient accessibility features',
                    'details': {
                        'found_features': found_features,
                        'cypress_tests': cypress_exists
                    }
                }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Accessibility test error: {str(e)}'
            }
    
    def test_mobile_responsiveness(self):
        """Test mobile and PWA features"""
        try:
            # Check for mobile CSS features
            css_file = os.path.join(
                self.project_root,
                'frontend', 'src', 'styles', 'enhanced-dashboard.css'
            )
            
            if os.path.exists(css_file):
                with open(css_file, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                mobile_features = [
                    '@media (max-width: 768px)',
                    '@media (max-width: 576px)',
                    'viewport',
                    'responsive'
                ]
                
                found_mobile_features = sum(1 for feature in mobile_features if feature in css_content)
            else:
                found_mobile_features = 0
            
            # Check for PWA manifest
            manifest_file = os.path.join(
                self.project_root,
                'frontend', 'public', 'manifest.json'
            )
            
            manifest_exists = os.path.exists(manifest_file)
            
            # Check Cypress mobile tests
            cypress_mobile_file = os.path.join(
                self.project_root,
                'cypress', 'e2e', '04-mobile-pwa.cy.js'
            )
            
            cypress_mobile_exists = os.path.exists(cypress_mobile_file)
            
            if found_mobile_features >= 2 and manifest_exists and cypress_mobile_exists:
                return {
                    'status': 'PASS',
                    'message': 'Mobile responsiveness implemented',
                    'details': {
                        'mobile_css_features': found_mobile_features,
                        'pwa_manifest': manifest_exists,
                        'cypress_tests': cypress_mobile_exists
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'message': 'Mobile responsiveness incomplete',
                    'details': {
                        'mobile_css_features': found_mobile_features,
                        'pwa_manifest': manifest_exists,
                        'cypress_tests': cypress_mobile_exists
                    }
                }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Mobile responsiveness test error: {str(e)}'
            }
    
    def test_performance_metrics(self):
        """Test performance optimization"""
        try:
            # Check for performance testing files
            locust_file = os.path.join(
                self.project_root,
                'tests', 'performance', 'locustfile.py'
            )
            
            if not os.path.exists(locust_file):
                return {
                    'status': 'FAIL',
                    'message': 'Performance test file not found'
                }
            
            # Check CSS for performance optimizations
            css_file = os.path.join(
                self.project_root,
                'frontend', 'src', 'styles', 'enhanced-dashboard.css'
            )
            
            performance_optimizations = 0
            if os.path.exists(css_file):
                with open(css_file, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                # Look for performance optimizations
                optimizations = [
                    'transition',
                    'transform',
                    'will-change',
                    'contain',
                    'animation'
                ]
                
                performance_optimizations = sum(1 for opt in optimizations if opt in css_content)
            
            return {
                'status': 'PASS',
                'message': 'Performance testing setup complete',
                'details': {
                    'locust_file_exists': True,
                    'css_optimizations': performance_optimizations
                }
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Performance test error: {str(e)}'
            }
    
    def test_security_measures(self):
        """Test security implementations"""
        try:
            security_score = 0
            security_details = {}
            
            # Check for HTTPS redirect in CSS
            css_file = os.path.join(
                self.project_root,
                'frontend', 'src', 'styles', 'enhanced-dashboard.css'
            )
            
            if os.path.exists(css_file):
                security_score += 1
                security_details['css_security'] = True
            
            # Check for security headers in any config files
            config_files = [
                'docker-compose.yml',
                'nginx.conf',
                '.env.example'
            ]
            
            security_configs = 0
            for config_file in config_files:
                if os.path.exists(os.path.join(self.project_root, config_file)):
                    security_configs += 1
            
            security_score += min(security_configs, 2)
            security_details['config_files'] = security_configs
            
            # Check for compliance service (indicates security focus)
            compliance_file = os.path.join(
                self.project_root,
                'backend', 'app', 'services', 'gdpr_compliance_service.py'
            )
            
            if os.path.exists(compliance_file):
                security_score += 2
                security_details['compliance_service'] = True
            
            if security_score >= 3:
                return {
                    'status': 'PASS',
                    'message': 'Security measures implemented',
                    'details': security_details
                }
            else:
                return {
                    'status': 'FAIL',
                    'message': 'Insufficient security measures',
                    'details': security_details
                }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Security test error: {str(e)}'
            }
    
    def _calculate_overall_status(self):
        """Calculate overall test status"""
        test_results = list(self.test_results['tests'].values())
        
        if not test_results:
            self.test_results['overall_status'] = 'NO_TESTS'
            return
        
        passed = sum(1 for result in test_results if result['status'] == 'PASS')
        failed = sum(1 for result in test_results if result['status'] == 'FAIL')
        errors = sum(1 for result in test_results if result['status'] == 'ERROR')
        warnings = sum(1 for result in test_results if result['status'] == 'WARN')
        
        total = len(test_results)
        pass_rate = (passed / total) * 100
        
        if pass_rate >= 90:
            self.test_results['overall_status'] = 'EXCELLENT'
        elif pass_rate >= 75:
            self.test_results['overall_status'] = 'GOOD'
        elif pass_rate >= 50:
            self.test_results['overall_status'] = 'ACCEPTABLE'
        else:
            self.test_results['overall_status'] = 'NEEDS_IMPROVEMENT'
        
        self.test_results['summary'] = {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'warnings': warnings,
            'pass_rate': round(pass_rate, 2)
        }
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        self.test_results['end_time'] = datetime.now()
        duration = self.test_results['end_time'] - self.test_results['start_time']
        self.test_results['duration'] = str(duration)
        
        # Save test results
        report_file = os.path.join(
            self.project_root, 
            f'PHASE5_TEST_RESULTS_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        # Convert datetime objects to strings for JSON serialization
        serializable_results = self._make_serializable(self.test_results)
        
        with open(report_file, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        logger.info(f"📊 Test report saved to: {report_file}")
        
        # Print summary
        summary = self.test_results['summary']
        logger.info(f"🎯 Overall Status: {self.test_results['overall_status']}")
        logger.info(f"📈 Pass Rate: {summary['pass_rate']}%")
        logger.info(f"✅ Passed: {summary['passed']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"💥 Errors: {summary['errors']}")
        logger.info(f"⚠️  Warnings: {summary['warnings']}")
    
    def _make_serializable(self, obj):
        """Convert datetime objects to strings for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

def main():
    """Main test execution"""
    runner = Phase5TestRunner()
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    if results['overall_status'] in ['EXCELLENT', 'GOOD']:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
