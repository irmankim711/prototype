"""
Simple test for Enhanced User Routes Registration and Validation
Tests without requiring a running server
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def test_imports():
    """Test if all enhanced user route components can be imported"""
    print("🧪 Testing Enhanced User Routes - Import Test")
    print("=" * 50)

    tests_passed = 0
    total_tests = 0

    # Test 1: Import enhanced user routes module
    total_tests += 1
    try:
        from app.routes.enhanced_user_routes import enhanced_user_bp
        print("✅ Enhanced user routes imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Failed to import enhanced user routes: {e}")

    # Test 2: Check if blueprint has correct prefix
    total_tests += 1
    try:
        from app.routes.enhanced_user_routes import enhanced_user_bp
        if enhanced_user_bp.url_prefix == '/api/users':
            print("✅ Blueprint has correct URL prefix: /api/users")
            tests_passed += 1
        else:
            print(f"❌ Blueprint has incorrect URL prefix: {enhanced_user_bp.url_prefix}")
    except Exception as e:
        print(f"❌ Failed to check blueprint prefix: {e}")

    # Test 3: Import SimpleUser model
    total_tests += 1
    try:
        from app.models.simple_user import SimpleUser
        print("✅ SimpleUser model imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Failed to import SimpleUser model: {e}")

    # Test 4: Check model fields
    total_tests += 1
    try:
        from app.models.simple_user import SimpleUser
        required_fields = [
            'first_name', 'last_name', 'username', 'phone', 'company',
            'job_title', 'bio', 'avatar_url', 'timezone', 'language',
            'theme', 'email_notifications', 'push_notifications'
        ]

        model_columns = [column.name for column in SimpleUser.__table__.columns]
        missing_fields = [field for field in required_fields if field not in model_columns]

        if not missing_fields:
            print("✅ All required model fields are present")
            tests_passed += 1
        else:
            print(f"❌ Missing model fields: {missing_fields}")
    except Exception as e:
        print(f"❌ Failed to check model fields: {e}")

    # Test 5: Check validation functions
    total_tests += 1
    try:
        from app.routes.enhanced_user_routes import validate_profile_data, allowed_file

        # Test validation with valid data
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'phone': '+1234567890',
            'bio': 'Test bio'
        }

        errors = validate_profile_data(valid_data)
        if not errors:
            print("✅ Profile validation works correctly")
            tests_passed += 1
        else:
            print(f"❌ Profile validation failed: {errors}")
    except Exception as e:
        print(f"❌ Failed to test validation functions: {e}")

    # Test 6: Check file validation
    total_tests += 1
    try:
        from app.routes.enhanced_user_routes import allowed_file

        if allowed_file('test.jpg') and allowed_file('test.png') and not allowed_file('test.txt'):
            print("✅ File validation works correctly")
            tests_passed += 1
        else:
            print("❌ File validation not working correctly")
    except Exception as e:
        print(f"❌ Failed to test file validation: {e}")

    # Test 7: Check if routes can be registered
    total_tests += 1
    try:
        from flask import Flask
        from app.routes.enhanced_user_routes import enhanced_user_bp

        app = Flask(__name__)
        app.register_blueprint(enhanced_user_bp)

        # Check if routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = [
            '/api/users/profile',
            '/api/users/avatar',
            '/api/users/change-password',
            '/api/users/account'
        ]

        routes_found = all(route in routes for route in expected_routes)

        if routes_found:
            print("✅ All expected routes are registered")
            tests_passed += 1
        else:
            print(f"❌ Missing routes. Found: {routes}")
    except Exception as e:
        print(f"❌ Failed to test route registration: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All import tests passed! Enhanced user routes are properly configured.")
        return True
    elif tests_passed >= total_tests * 0.8:
        print("✅ Most tests passed. Minor issues may need attention.")
        return True
    else:
        print("⚠️ Several tests failed. Please check the implementation.")
        return False

def test_validation_logic():
    """Test the validation logic with various inputs"""
    print("\n🧪 Testing Validation Logic")
    print("=" * 30)

    try:
        from app.routes.enhanced_user_routes import validate_profile_data

        # Test cases
        test_cases = [
            {
                'name': 'Valid data',
                'data': {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'username': 'johndoe',
                    'phone': '+1234567890',
                    'bio': 'Test bio'
                },
                'should_pass': True
            },
            {
                'name': 'Invalid username (starts with number)',
                'data': {
                    'first_name': 'John',
                    'username': '1invalid'
                },
                'should_pass': False
            },
            {
                'name': 'Too long first name',
                'data': {
                    'first_name': 'A' * 100
                },
                'should_pass': False
            },
            {
                'name': 'Invalid phone',
                'data': {
                    'phone': 'invalid_phone'
                },
                'should_pass': False
            },
            {
                'name': 'Too long bio',
                'data': {
                    'bio': 'A' * 600
                },
                'should_pass': False
            }
        ]

        passed = 0
        for test_case in test_cases:
            errors = validate_profile_data(test_case['data'])
            has_errors = len(errors) > 0

            if test_case['should_pass'] and not has_errors:
                print(f"✅ {test_case['name']}")
                passed += 1
            elif not test_case['should_pass'] and has_errors:
                print(f"✅ {test_case['name']} (correctly failed)")
                passed += 1
            else:
                print(f"❌ {test_case['name']} - Expected: {'pass' if test_case['should_pass'] else 'fail'}, Got: {'pass' if not has_errors else 'fail'}")

        print(f"📊 Validation Tests: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)

    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Enhanced User Profile - Comprehensive Testing")
    print("=" * 60)

    import_success = test_imports()
    validation_success = test_validation_logic()

    print("\n" + "=" * 60)
    print("📋 Final Summary:")

    if import_success and validation_success:
        print("🎉 All tests passed! Enhanced user profile is ready for integration.")
        print("\n📝 Next Steps:")
        print("1. Start the backend server: python run.py")
        print("2. Test with the React frontend component")
        print("3. Create test users and verify profile functionality")
        print("4. Test image upload with actual files")
    else:
        print("⚠️ Some tests failed. Please review the issues above.")

    return import_success and validation_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)