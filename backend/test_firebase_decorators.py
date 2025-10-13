"""
Test Firebase-integrated decorators
Tests for task 2.2: Validate permission system integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from flask import Flask, g, jsonify
from datetime import datetime

# Create a minimal Flask app for testing
app = Flask(__name__)
app.config['TESTING'] = True

def test_firebase_decorators():
    """Test Firebase-integrated decorators"""
    
    from app.models.production.user_models import User
    from app.models.production.permissions import UserRole, Permission
    from app.decorators import require_permission, require_role, get_current_user, get_current_user_id
    
    print("Testing Firebase-integrated decorators...")
    
    with app.app_context():
        # Create test users
        admin_user = User(
            id=1,
            email='admin@example.com',
            firebase_uid='admin_uid_123',
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            is_active=True
        )
        
        regular_user = User(
            id=2,
            email='user@example.com',
            firebase_uid='user_uid_456',
            first_name='Regular',
            last_name='User',
            role=UserRole.USER,
            is_active=True
        )
        
        viewer_user = User(
            id=3,
            email='viewer@example.com',
            firebase_uid='viewer_uid_789',
            first_name='Viewer',
            last_name='User',
            role=UserRole.VIEWER,
            is_active=True
        )
        
        inactive_user = User(
            id=4,
            email='inactive@example.com',
            firebase_uid='inactive_uid_000',
            first_name='Inactive',
            last_name='User',
            role=UserRole.USER,
            is_active=False
        )
        
        # Test 1: get_current_user and get_current_user_id functions
        with app.test_request_context():
            # No user in context
            assert get_current_user() is None, "Should return None when no user in context"
            assert get_current_user_id() is None, "Should return None when no user in context"
            
            # User in context
            g.current_user = admin_user
            assert get_current_user() == admin_user, "Should return user from context"
            assert get_current_user_id() == 1, "Should return user ID from context"
            print("✅ Test 1 passed: get_current_user functions work with Firebase context")
        
        # Test 2: require_permission decorator with admin user
        @require_permission(Permission.ADMIN)
        def admin_only_endpoint():
            return jsonify({'message': 'Admin access granted'})
        
        with app.test_request_context():
            g.current_user = admin_user
            response = admin_only_endpoint()
            assert response.status_code == 200, "Admin should have access to admin endpoint"
            print("✅ Test 2 passed: require_permission allows admin user")
        
        # Test 3: require_permission decorator denies regular user
        with app.test_request_context():
            g.current_user = regular_user
            response, status_code = admin_only_endpoint()
            assert status_code == 403, "Regular user should be denied admin endpoint"
            print("✅ Test 3 passed: require_permission denies regular user")
        
        # Test 4: require_permission with no user
        with app.test_request_context():
            # Ensure no user in context
            if hasattr(g, 'current_user'):
                delattr(g, 'current_user')
            result = admin_only_endpoint()
            print(f"Debug: admin_only_endpoint() returned: {result}, type: {type(result)}")
            if isinstance(result, tuple):
                response, status_code = result
                assert status_code == 401, f"Should require authentication, got {status_code}"
            else:
                # It's a Response object
                assert result.status_code == 401, f"Should require authentication, got {result.status_code}"
            print("✅ Test 4 passed: require_permission requires authentication")
        
        # Test 5: require_permission with inactive user
        with app.test_request_context():
            g.current_user = inactive_user
            response, status_code = admin_only_endpoint()
            assert status_code == 401, "Inactive user should be denied"
            print("✅ Test 5 passed: require_permission denies inactive user")
        
        # Test 6: require_role decorator with single role
        @require_role(UserRole.ADMIN)
        def admin_role_endpoint():
            return jsonify({'message': 'Admin role access granted'})
        
        with app.test_request_context():
            g.current_user = admin_user
            response = admin_role_endpoint()
            assert response.status_code == 200, "Admin should have access to admin role endpoint"
            print("✅ Test 6 passed: require_role allows correct single role")
        
        # Test 7: require_role decorator with multiple roles
        @require_role([UserRole.ADMIN, UserRole.USER])
        def multi_role_endpoint():
            return jsonify({'message': 'Multi-role access granted'})
        
        with app.test_request_context():
            g.current_user = regular_user
            response = multi_role_endpoint()
            assert response.status_code == 200, "User should have access to multi-role endpoint"
            print("✅ Test 7 passed: require_role allows user in multi-role list")
        
        with app.test_request_context():
            g.current_user = admin_user
            response = multi_role_endpoint()
            assert response.status_code == 200, "Admin should have access to multi-role endpoint"
            print("✅ Test 8 passed: require_role allows admin in multi-role list")
        
        # Test 9: require_role denies viewer
        with app.test_request_context():
            g.current_user = viewer_user
            response, status_code = multi_role_endpoint()
            assert status_code == 403, "Viewer should be denied multi-role endpoint"
            print("✅ Test 9 passed: require_role denies viewer from multi-role endpoint")
        
        # Test 10: Combined decorators
        @require_permission(Permission.WRITE)
        @require_role([UserRole.ADMIN, UserRole.USER])
        def combined_endpoint():
            return jsonify({'message': 'Combined access granted'})
        
        with app.test_request_context():
            g.current_user = regular_user
            response = combined_endpoint()
            assert response.status_code == 200, "User with WRITE permission should have access"
            print("✅ Test 10 passed: Combined decorators work correctly")
        
        with app.test_request_context():
            g.current_user = viewer_user
            response, status_code = combined_endpoint()
            assert status_code == 403, "Viewer without WRITE permission should be denied"
            print("✅ Test 11 passed: Combined decorators deny insufficient permissions")
        
        print("\n🎉 All Firebase decorator tests passed!")

if __name__ == '__main__':
    test_firebase_decorators()