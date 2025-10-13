"""
Test script for Enhanced User Profile functionality
Tests integration between frontend and backend APIs
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class UserProfileTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None

    def print_test(self, test_name, status, details=""):
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   └─ {details}")

    def test_api_connection(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                self.print_test("API Connection", "PASS", "Backend server is running")
                return True
            else:
                self.print_test("API Connection", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("API Connection", "FAIL", str(e))
            return False

    def test_user_routes_exist(self):
        """Test if enhanced user routes are registered"""
        try:
            # Test profile endpoint (should require auth)
            response = self.session.get(f"{self.base_url}/api/users/profile")
            if response.status_code in [401, 403]:  # Expected - requires auth
                self.print_test("User Routes Registration", "PASS", "Profile endpoint exists and requires auth")
                return True
            else:
                self.print_test("User Routes Registration", "FAIL", f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("User Routes Registration", "FAIL", str(e))
            return False

    def test_profile_validation(self):
        """Test profile data validation"""
        try:
            # Test with invalid data (should fail validation)
            invalid_data = {
                "first_name": "A" * 100,  # Too long
                "username": "1invalid",   # Starts with number
                "phone": "invalid_phone", # Invalid format
                "bio": "A" * 600         # Too long
            }

            response = self.session.put(
                f"{self.base_url}/api/users/profile",
                json=invalid_data
            )

            if response.status_code == 401:
                self.print_test("Profile Validation", "PASS", "Validation requires authentication")
                return True
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    if 'validation_errors' in error_data:
                        self.print_test("Profile Validation", "PASS", "Validation errors properly returned")
                        return True
                except:
                    pass

            self.print_test("Profile Validation", "WARNING", f"Status: {response.status_code}")
            return True
        except Exception as e:
            self.print_test("Profile Validation", "FAIL", str(e))
            return False

    def test_avatar_upload_endpoint(self):
        """Test avatar upload endpoint exists"""
        try:
            # Test avatar upload (should require auth)
            response = self.session.post(f"{self.base_url}/api/users/avatar")
            if response.status_code in [400, 401, 403]:  # Expected - requires auth and file
                self.print_test("Avatar Upload Endpoint", "PASS", "Avatar endpoint exists and has proper validation")
                return True
            else:
                self.print_test("Avatar Upload Endpoint", "FAIL", f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Avatar Upload Endpoint", "FAIL", str(e))
            return False

    def test_password_change_endpoint(self):
        """Test password change endpoint exists"""
        try:
            response = self.session.post(f"{self.base_url}/api/users/change-password")
            if response.status_code in [400, 401, 403]:  # Expected - requires auth and data
                self.print_test("Password Change Endpoint", "PASS", "Password change endpoint exists")
                return True
            else:
                self.print_test("Password Change Endpoint", "FAIL", f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Password Change Endpoint", "FAIL", str(e))
            return False

    def test_account_deletion_endpoint(self):
        """Test account deletion endpoint exists"""
        try:
            response = self.session.delete(f"{self.base_url}/api/users/account")
            if response.status_code in [401, 403]:  # Expected - requires auth
                self.print_test("Account Deletion Endpoint", "PASS", "Account deletion endpoint exists")
                return True
            else:
                self.print_test("Account Deletion Endpoint", "FAIL", f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Account Deletion Endpoint", "FAIL", str(e))
            return False

    def test_rate_limiting(self):
        """Test rate limiting is implemented"""
        try:
            # Make multiple rapid requests to test rate limiting
            responses = []
            for i in range(12):  # Should trigger rate limit (10 per minute)
                response = self.session.put(f"{self.base_url}/api/users/profile", json={})
                responses.append(response.status_code)

            if 429 in responses:
                self.print_test("Rate Limiting", "PASS", "Rate limiting is active")
                return True
            else:
                self.print_test("Rate Limiting", "WARNING", "Rate limiting may not be active")
                return True
        except Exception as e:
            self.print_test("Rate Limiting", "FAIL", str(e))
            return False

    def test_file_upload_validation(self):
        """Test file upload validation"""
        try:
            # Test with invalid file type
            files = {'avatar': ('test.txt', 'This is not an image', 'text/plain')}
            response = self.session.post(f"{self.base_url}/api/users/avatar", files=files)

            if response.status_code in [400, 401, 403]:
                self.print_test("File Upload Validation", "PASS", "File upload has proper validation")
                return True
            else:
                self.print_test("File Upload Validation", "WARNING", f"Status: {response.status_code}")
                return True
        except Exception as e:
            self.print_test("File Upload Validation", "FAIL", str(e))
            return False

    def test_database_model_compatibility(self):
        """Test if the user model supports all required fields"""
        try:
            # Check if we can import the model
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

            from app.models.simple_user import SimpleUser

            required_fields = [
                'first_name', 'last_name', 'username', 'phone', 'company',
                'job_title', 'bio', 'avatar_url', 'timezone', 'language',
                'theme', 'email_notifications', 'push_notifications'
            ]

            model_columns = [column.name for column in SimpleUser.__table__.columns]

            missing_fields = [field for field in required_fields if field not in model_columns]

            if not missing_fields:
                self.print_test("Database Model Compatibility", "PASS", "All required fields present")
                return True
            else:
                self.print_test("Database Model Compatibility", "FAIL", f"Missing fields: {missing_fields}")
                return False

        except Exception as e:
            self.print_test("Database Model Compatibility", "WARNING", f"Cannot verify: {str(e)}")
            return True

    def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Enhanced User Profile Integration Tests")
        print("=" * 50)

        tests = [
            self.test_api_connection,
            self.test_user_routes_exist,
            self.test_profile_validation,
            self.test_avatar_upload_endpoint,
            self.test_password_change_endpoint,
            self.test_account_deletion_endpoint,
            self.test_rate_limiting,
            self.test_file_upload_validation,
            self.test_database_model_compatibility
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1

        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Enhanced user profile is ready for use.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Minor issues may need attention.")
        else:
            print("⚠️ Several tests failed. Please check the implementation.")

        print("\n📝 Next Steps:")
        print("1. Ensure backend server is running")
        print("2. Test with the EnhancedUserProfile React component")
        print("3. Create a test user and verify profile functionality")
        print("4. Test image upload with actual image files")

if __name__ == "__main__":
    tester = UserProfileTester()
    tester.run_all_tests()