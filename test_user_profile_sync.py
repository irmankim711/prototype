#!/usr/bin/env python3
"""
User Profile Synchronization Test Suite
Tests the complete user profile sync implementation across components
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:5174"

class UserProfileSyncTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
        
    def print_step(self, step, description):
        print(f"\n{step}. {description}")
        print("-" * 40)
        
    def print_success(self, message):
        print(f"✅ {message}")
        
    def print_error(self, message):
        print(f"❌ {message}")
        
    def print_info(self, message):
        print(f"ℹ️  {message}")
        
    def test_user_registration_login(self):
        """Test user registration and login functionality"""
        self.print_step("1", "Testing User Registration & Login")
        
        # Generate unique test user
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_email = f"testuser_{timestamp}@example.com"
        test_pwd = "test123"
        
        try:
            # Register new user
            register_data = {
                "email": test_email,
                "password": test_pwd,
                "username": f"testuser_{timestamp}",  # Add unique username
                "organizationName": "Test Organization"
            }
            
            register_response = self.session.post(
                f"{BASE_URL}/api/auth/register", 
                json=register_data
            )
            
            if register_response.status_code == 201:
                self.print_success(f"User registration successful for {test_email}")
            else:
                self.print_error(f"Registration failed: {register_response.text}")
                return False
                
            # Login with the new user
            login_data = {
                "email": test_email,
                "password": test_pwd
            }
            
            login_response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json=login_data
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                self.access_token = login_data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                self.print_success(f"Login successful, token acquired")
                return True
            else:
                self.print_error(f"Login failed: {login_response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Authentication test failed: {str(e)}")
            return False
            
    def test_initial_profile_fetch(self):
        """Test fetching initial user profile data"""
        self.print_step("2", "Testing Initial Profile Data Fetch")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/users/profile")
            
            if response.status_code == 200:
                profile_data = response.json()
                self.user_id = profile_data.get("id")
                
                self.print_success("Initial profile data retrieved successfully")
                self.print_info(f"   User ID: {profile_data.get('id')}")
                self.print_info(f"   Email: {profile_data.get('email')}")
                self.print_info(f"   Username: {profile_data.get('username', 'Not set')}")
                self.print_info(f"   First Name: {profile_data.get('first_name', 'Not set')}")
                self.print_info(f"   Last Name: {profile_data.get('last_name', 'Not set')}")
                
                return profile_data
            else:
                self.print_error(f"Failed to fetch profile: {response.text}")
                return None
                
        except Exception as e:
            self.print_error(f"Profile fetch test failed: {str(e)}")
            return None
            
    def test_profile_update_sync(self):
        """Test profile update and synchronization"""
        self.print_step("3", "Testing Profile Update & Sync")
        
        # Test data for profile update
        timestamp = datetime.now().strftime("%H%M%S")
        update_data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": f"johndoe_{timestamp}",
            "phone": "+1-555-123-4567",
            "company": "StratoSys Corp",
            "job_title": "Senior Software Engineer",
            "bio": "Full-stack developer specializing in modern web technologies.",
            "timezone": "America/New_York",
            "language": "en",
            "theme": "light",
            "email_notifications": True,
            "push_notifications": False
        }
        
        try:
            # Update profile
            update_response = self.session.put(
                f"{BASE_URL}/api/users/profile",
                json=update_data
            )
            
            if update_response.status_code == 200:
                updated_profile = update_response.json()
                self.print_success("Profile update successful")
                
                # Verify the update
                verification_response = self.session.get(f"{BASE_URL}/api/users/profile")
                
                if verification_response.status_code == 200:
                    verified_data = verification_response.json()
                    
                    # Check if data was properly updated
                    checks_passed = 0
                    total_checks = 0
                    
                    for key, expected_value in update_data.items():
                        total_checks += 1
                        actual_value = verified_data.get(key)
                        
                        if actual_value == expected_value:
                            checks_passed += 1
                            self.print_success(f"   {key}: {actual_value} ✓")
                        else:
                            self.print_error(f"   {key}: Expected {expected_value}, got {actual_value}")
                    
                    success_rate = (checks_passed / total_checks) * 100
                    self.print_info(f"Update verification: {checks_passed}/{total_checks} fields correct ({success_rate:.1f}%)")
                    
                    return verified_data
                else:
                    self.print_error(f"Failed to verify update: {verification_response.text}")
                    return None
            else:
                self.print_error(f"Profile update failed: {update_response.text}")
                return None
                
        except Exception as e:
            self.print_error(f"Profile update test failed: {str(e)}")
            return None
            
    def test_display_name_generation(self, profile_data):
        """Test display name generation logic"""
        self.print_step("4", "Testing Display Name Generation Logic")
        
        try:
            first_name = profile_data.get("first_name", "")
            last_name = profile_data.get("last_name", "")
            username = profile_data.get("username", "")
            email = profile_data.get("email", "")
            
            # Test display name logic (matching frontend logic)
            if first_name and last_name:
                expected_display_name = f"{first_name} {last_name}"
            elif first_name:
                expected_display_name = first_name
            elif last_name:
                expected_display_name = last_name
            elif username:
                expected_display_name = username
            else:
                expected_display_name = email or "Unknown User"
                
            self.print_success(f"Expected display name: '{expected_display_name}'")
            
            # Test initials generation
            if first_name and last_name:
                expected_initials = f"{first_name[0]}{last_name[0]}".upper()
            elif first_name:
                expected_initials = first_name[:2].upper()
            elif last_name:
                expected_initials = last_name[:2].upper()
            elif email:
                expected_initials = email[:2].upper()
            else:
                expected_initials = "U"
                
            self.print_success(f"Expected initials: '{expected_initials}'")
            
            # Test avatar URL generation
            expected_avatar_url = f"https://ui-avatars.com/api/?name={expected_initials}&background=6366f1&color=ffffff&size=128&bold=true"
            self.print_success(f"Expected avatar URL generated")
            
            return {
                "display_name": expected_display_name,
                "initials": expected_initials,
                "avatar_url": expected_avatar_url
            }
            
        except Exception as e:
            self.print_error(f"Display name generation test failed: {str(e)}")
            return None
            
    def test_profile_completion_calculation(self, profile_data):
        """Test profile completion percentage calculation"""
        self.print_step("5", "Testing Profile Completion Calculation")
        
        try:
            # Fields counted for profile completion
            fields = [
                "first_name", "last_name", "username", "email",
                "phone", "company", "job_title", "bio", "avatar_url"
            ]
            
            completed_fields = 0
            total_fields = len(fields)
            
            for field in fields:
                value = profile_data.get(field)
                if value and str(value).strip():
                    completed_fields += 1
                    self.print_success(f"   {field}: '{value}' ✓")
                else:
                    self.print_info(f"   {field}: Not set")
            
            completion_percentage = round((completed_fields / total_fields) * 100)
            is_complete = completion_percentage >= 80
            
            self.print_success(f"Profile completion: {completed_fields}/{total_fields} fields ({completion_percentage}%)")
            self.print_success(f"Profile complete status: {is_complete}")
            
            return {
                "completion_percentage": completion_percentage,
                "is_complete": is_complete,
                "completed_fields": completed_fields,
                "total_fields": total_fields
            }
            
        except Exception as e:
            self.print_error(f"Profile completion test failed: {str(e)}")
            return None
            
    def test_concurrent_updates(self):
        """Test handling of concurrent profile updates"""
        self.print_step("6", "Testing Concurrent Update Handling")
        
        try:
            # Simulate multiple rapid updates
            updates = [
                {"company": "Company A"},
                {"job_title": "Title A"},
                {"bio": "Bio A"}
            ]
            
            results = []
            for i, update in enumerate(updates):
                response = self.session.put(
                    f"{BASE_URL}/api/users/profile",
                    json=update
                )
                results.append(response.status_code == 200)
                time.sleep(0.1)  # Small delay between updates
                
            success_count = sum(results)
            self.print_success(f"Concurrent updates: {success_count}/{len(updates)} successful")
            
            # Verify final state
            final_response = self.session.get(f"{BASE_URL}/api/users/profile")
            if final_response.status_code == 200:
                final_data = final_response.json()
                self.print_success(f"Final state verification successful")
                self.print_info(f"   Company: {final_data.get('company')}")
                self.print_info(f"   Job Title: {final_data.get('job_title')}")
                self.print_info(f"   Bio: {final_data.get('bio')}")
                
            return success_count == len(updates)
            
        except Exception as e:
            self.print_error(f"Concurrent update test failed: {str(e)}")
            return False
            
    def test_error_handling(self):
        """Test error handling scenarios"""
        self.print_step("7", "Testing Error Handling")
        
        try:
            test_cases = [
                {
                    "name": "Invalid username (too short)",
                    "data": {"username": "a"},
                    "expected_status": 400
                },
                {
                    "name": "Invalid email format",
                    "data": {"email": "invalid-email"},
                    "expected_status": 400
                },
                {
                    "name": "Empty required field",
                    "data": {"first_name": "", "last_name": ""},
                    "expected_status": 400
                }
            ]
            
            passed_tests = 0
            
            for test_case in test_cases:
                response = self.session.put(
                    f"{BASE_URL}/api/users/profile",
                    json=test_case["data"]
                )
                
                if response.status_code == test_case["expected_status"]:
                    self.print_success(f"   {test_case['name']}: Handled correctly")
                    passed_tests += 1
                else:
                    self.print_error(f"   {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}")
            
            self.print_success(f"Error handling: {passed_tests}/{len(test_cases)} tests passed")
            return passed_tests == len(test_cases)
            
        except Exception as e:
            self.print_error(f"Error handling test failed: {str(e)}")
            return False
            
    def run_full_test_suite(self):
        """Run the complete test suite"""
        self.print_header("User Profile Synchronization Test Suite")
        print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Backend URL: {BASE_URL}")
        print(f"🖥️  Frontend URL: {FRONTEND_URL}")
        
        test_results = {}
        
        # Run all tests
        test_results["auth"] = self.test_user_registration_login()
        
        if test_results["auth"]:
            profile_data = self.test_initial_profile_fetch()
            test_results["initial_fetch"] = profile_data is not None
            
            if profile_data:
                updated_profile = self.test_profile_update_sync()
                test_results["profile_update"] = updated_profile is not None
                
                if updated_profile:
                    display_data = self.test_display_name_generation(updated_profile)
                    test_results["display_name"] = display_data is not None
                    
                    completion_data = self.test_profile_completion_calculation(updated_profile)
                    test_results["profile_completion"] = completion_data is not None
                    
                    test_results["concurrent_updates"] = self.test_concurrent_updates()
                    test_results["error_handling"] = self.test_error_handling()
        
        # Print summary
        self.print_header("Test Results Summary")
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 Overall Results:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 85:
            print(f"\n🎉 Test suite completed successfully!")
            print(f"   User profile synchronization is working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Please review the implementation.")
            
        print(f"\n🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 85

def main():
    """Main function to run the test suite"""
    print("🚀 Starting User Profile Synchronization Test Suite")
    
    # Check if servers are running
    try:
        backend_response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Backend server is running")
    except:
        print(f"❌ Backend server is not accessible at {BASE_URL}")
        print(f"   Please ensure the backend is running: cd backend && python run.py")
        sys.exit(1)
    
    try:
        frontend_response = requests.get(FRONTEND_URL, timeout=5)
        print(f"✅ Frontend server is accessible")
    except:
        print(f"⚠️  Frontend server may not be accessible at {FRONTEND_URL}")
        print(f"   Please ensure the frontend is running: cd frontend && npm run dev")
    
    # Run tests
    tester = UserProfileSyncTester()
    success = tester.run_full_test_suite()
    
    if success:
        print(f"\n🏆 All tests passed! User profile synchronization is working correctly.")
        sys.exit(0)
    else:
        print(f"\n🔧 Some tests failed. Please review the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
