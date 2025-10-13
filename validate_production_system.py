"""
Production System Validation
Complete validation of the production-ready form automation platform
"""
import os
import sys
import requests
import json
import time
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class ProductionValidator:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.errors = []
        self.successes = []
        
    def validate_environment_setup(self) -> bool:
        """Validate production environment configuration"""
        logger.info("🔧 Validating Environment Setup...")
        
        required_files = [
            ".env.production",
            "app/services/production_google_forms_service.py",
            "app/services/production_ai_service.py", 
            "app/services/production_template_service.py",
            "app/routes/production_routes.py",
            "run_production.py"
        ]
        
        backend_path = os.path.join(os.getcwd(), "backend")
        
        for file_path in required_files:
            full_path = os.path.join(backend_path, file_path)
            if os.path.exists(full_path):
                self.successes.append(f"✅ {file_path} exists")
            else:
                self.errors.append(f"❌ Missing: {file_path}")
                
        # Check environment variables
        env_file = os.path.join(backend_path, ".env.production")
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_content = f.read()
                
            required_env_vars = [
                "GOOGLE_CLIENT_ID",
                "GOOGLE_CLIENT_SECRET", 
                "OPENAI_API_KEY",
                "MICROSOFT_CLIENT_ID",
                "JWT_SECRET_KEY",
                "MOCK_MODE_DISABLED=true"
            ]
            
            for var in required_env_vars:
                if var in env_content:
                    self.successes.append(f"✅ Environment variable: {var}")
                else:
                    self.errors.append(f"❌ Missing environment variable: {var}")
        
        return len(self.errors) == 0
    
    def validate_mock_elimination(self) -> bool:
        """Validate that mock data has been properly eliminated"""
        logger.info("🚫 Validating Mock Data Elimination...")
        
        # Check for mock patterns in production files
        production_files = [
            "backend/app/services/production_google_forms_service.py",
            "backend/app/services/production_ai_service.py",
            "backend/app/services/production_template_service.py",
            "backend/app/routes/production_routes.py"
        ]
        
        mock_patterns = [
            "return mock_",
            "mock_data =",
            "# TODO: Replace with real implementation",
            "hardcoded_sample"
        ]
        
        for file_path in production_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                for pattern in mock_patterns:
                    if pattern in content:
                        self.errors.append(f"❌ Mock pattern '{pattern}' found in {file_path}")
                    else:
                        self.successes.append(f"✅ No '{pattern}' in {file_path}")
        
        return len([e for e in self.errors if "Mock pattern" in e]) == 0
    
    def test_backend_health(self) -> bool:
        """Test backend server health"""
        logger.info("🏥 Testing Backend Health...")
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') == 'healthy':
                    self.successes.append("✅ Backend server is healthy")
                    
                    # Check production mode
                    if health_data.get('mock_disabled'):
                        self.successes.append("✅ Mock mode is disabled")
                    else:
                        self.errors.append("❌ Mock mode still enabled")
                        
                    return True
                else:
                    self.errors.append("❌ Backend unhealthy")
                    return False
            else:
                self.errors.append(f"❌ Backend health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.errors.append(f"❌ Backend not accessible: {str(e)}")
            return False
    
    def test_google_oauth_setup(self) -> bool:
        """Test Google OAuth configuration"""
        logger.info("🔐 Testing Google OAuth Setup...")
        
        try:
            response = requests.get(f"{self.backend_url}/api/production/auth/google/url", timeout=10)
            if response.status_code == 200:
                oauth_data = response.json()
                if 'auth_url' in oauth_data and 'accounts.google.com' in oauth_data['auth_url']:
                    self.successes.append("✅ Google OAuth URL generation working")
                    return True
                else:
                    self.errors.append("❌ Invalid Google OAuth URL")
                    return False
            else:
                self.errors.append(f"❌ Google OAuth setup failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.errors.append(f"❌ Google OAuth test failed: {str(e)}")
            return False
    
    def test_template_system(self) -> bool:
        """Test production template system"""
        logger.info("📄 Testing Template System...")
        
        try:
            response = requests.get(f"{self.backend_url}/api/production/templates", timeout=10)
            if response.status_code == 200:
                templates = response.json()
                if isinstance(templates, list) and len(templates) > 0:
                    self.successes.append(f"✅ Templates loaded: {len(templates)} available")
                    
                    # Check for real template data
                    for template in templates:
                        if 'name' in template and 'placeholders' in template:
                            self.successes.append(f"✅ Template '{template['name']}' has placeholders")
                        else:
                            self.errors.append(f"❌ Template missing required fields")
                    
                    return True
                else:
                    self.errors.append("❌ No templates available")
                    return False
            else:
                self.errors.append(f"❌ Template system failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.errors.append(f"❌ Template system test failed: {str(e)}")
            return False
    
    def test_production_apis(self) -> bool:
        """Test all production API endpoints"""
        logger.info("🚀 Testing Production APIs...")
        
        # Test endpoints that don't require authentication
        test_endpoints = [
            ("/api/production/health", "Health endpoint"),
            ("/api/production/templates", "Templates endpoint"),
            ("/api/production/auth/google/url", "Google OAuth URL"),
        ]
        
        success_count = 0
        for endpoint, description in test_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                if response.status_code in [200, 201]:
                    self.successes.append(f"✅ {description} working")
                    success_count += 1
                else:
                    self.errors.append(f"❌ {description} failed: {response.status_code}")
            except Exception as e:
                self.errors.append(f"❌ {description} error: {str(e)}")
        
        return success_count == len(test_endpoints)
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        total_tests = len(self.successes) + len(self.errors)
        success_rate = (len(self.successes) / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "validation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "successes": len(self.successes),
            "errors": len(self.errors),
            "success_rate": f"{success_rate:.1f}%",
            "production_ready": len(self.errors) == 0,
            "details": {
                "successes": self.successes,
                "errors": self.errors
            }
        }
        
        return report
    
    def run_full_validation(self) -> bool:
        """Run complete production validation"""
        logger.info("🎯 Starting Complete Production Validation")
        logger.info("=" * 60)
        
        # Run all validation tests
        tests = [
            ("Environment Setup", self.validate_environment_setup),
            ("Mock Data Elimination", self.validate_mock_elimination),
            ("Backend Health", self.test_backend_health),
            ("Google OAuth Setup", self.test_google_oauth_setup),
            ("Template System", self.test_template_system),
            ("Production APIs", self.test_production_apis)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.errors.append(f"❌ {test_name} crashed: {str(e)}")
            logger.info("")
        
        # Generate report
        report = self.generate_validation_report()
        
        # Save report
        with open("PRODUCTION_VALIDATION_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("📋 PRODUCTION VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {report['total_tests']}")
        logger.info(f"Successes: {report['successes']}")
        logger.info(f"Errors: {report['errors']}")
        logger.info(f"Success Rate: {report['success_rate']}")
        logger.info(f"Production Ready: {'✅ YES' if report['production_ready'] else '❌ NO'}")
        
        if self.errors:
            logger.info("\n🚨 ERRORS TO RESOLVE:")
            for error in self.errors:
                logger.info(f"  {error}")
        
        if self.successes:
            logger.info("\n✅ SUCCESSFUL VALIDATIONS:")
            for success in self.successes[:10]:  # Show first 10
                logger.info(f"  {success}")
            if len(self.successes) > 10:
                logger.info(f"  ... and {len(self.successes) - 10} more")
        
        return report['production_ready']

def main():
    """Main validation function"""
    validator = ProductionValidator()
    
    logger.info("🚀 PRODUCTION SYSTEM VALIDATION")
    logger.info("Testing the complete elimination of mock data")
    logger.info("and validation of production-ready implementation")
    logger.info("")
    
    success = validator.run_full_validation()
    
    if success:
        logger.info("\n🎉 PRODUCTION VALIDATION COMPLETE!")
        logger.info("✅ Your system is production-ready!")
        logger.info("🚀 All mock data has been eliminated!")
        return 0
    else:
        logger.info("\n⚠️ PRODUCTION VALIDATION INCOMPLETE")
        logger.info("❌ Please resolve the errors above")
        logger.info("📋 Check PRODUCTION_VALIDATION_REPORT.json for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
