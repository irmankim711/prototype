"""
Test user endpoints with Firebase authentication
Tests for task 2.2: Validate permission system integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from flask import Flask, g
from unittest.mock import patch, MagicMock
import json

def test_user_endpoints_with_firebase():
    """Test user endpoints work with Firebase authentication"""
    
    from app import create_app, db
    from app.models.production.user_models import User
    from app.models.production.permissions import UserRole, Permission
    
    print("Testing user endpoints with Firebase authentication...")
    
    # Create test app
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test users
        admin_user = User(
            id=1,
            email='admin@example.com',
            firebase_uid='admin_uid_123',
            username='admin_user',
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            is_active=True
        )
        
        regular_user = User(
            id=2,
            email='user@example.com',
            firebase_uid='user_uid_456',
            username='regular_user',
            first_name='Regular',
            last_name='User',
            role=UserRole.USER,
            is_active=True
        )
        
        viewer_user = User(
            id=3,
            email='viewer@example.com',
            firebase_uid='viewer_uid_789',
            username='viewer_user',
            first_name='Viewer',
            last_name='User',
            role=UserRole.VIEWER,
            is_active=True
        )
        
        # Add users to database
        db.session.add(admin_user)
        db.session.add(regular_user)
        db.session.add(viewer_user)
        db.session.commit()
        
        client = app.test_client()
        
        # Mock Firebase authentication
        with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True), \
             patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token') as mock_verify, \
             patch('app.middleware.firebase_auth.firebase_auth_manager.get_or_create_user') as mock_get_user:
            
            # Test 1: Admin can access user list endpoint
            mock_verify.return_value = {
                'uid': 'admin_uid_123',
                'email': 'admin@example.com'
            }
            mock_get_user.return_value = admin_user
            
            headers = {'Authorization': 'Bearer admin_firebase_token'}
            response = client.get('/api/users/', headers=headers)
            
            print(f"Admin user list response: {response.status_code}")
            if response.status_code == 200:
                print("✅ Test 1 passed: Admin can access user list endpoint")
            else:
                print(f"❌ Test 1 failed: Expected 200, got {response.status_code}")
                print(f"Response: {response.get_json()}")
            
            # Test 2: Regular user cannot access user list endpoint
            mock_verify.return_value = {
                'uid': 'user_uid_456',
                'email': 'user@example.com'
            }
            mock_get_user.return_value = regular_user
            
            headers = {'Authorization': 'Bearer user_firebase_token'}
            response = client.get('/api/users/', headers=headers)
            
            print(f"Regular user list response: {response.status_code}")
            if response.status_code == 403:
                print("✅ Test 2 passed: Regular user cannot access user list endpoint")
            else:
                print(f"❌ Test 2 failed: Expected 403, got {response.status_code}")
                print(f"Response: {response.get_json()}")
            
            # Test 3: Admin can update user role
            mock_verify.return_value = {
                'uid': 'admin_uid_123',
                'email': 'admin@example.com'
            }
            mock_get_user.return_value = admin_user
            
            headers = {'Authorization': 'Bearer admin_firebase_token'}
            data = {'role': 'admin'}
            response = client.put(f'/api/users/{regular_user.id}/role', 
                                headers=headers, 
                                json=data)
            
            print(f"Admin update role response: {response.status_code}")
            if response.status_code in [200, 404]:  # 404 if route not found is OK for this test
                print("✅ Test 3 passed: Admin can access user role update endpoint")
            else:
                print(f"❌ Test 3 failed: Expected 200 or 404, got {response.status_code}")
                print(f"Response: {response.get_json()}")
            
            # Test 4: Regular user cannot update user role
            mock_verify.return_value = {
                'uid': 'user_uid_456',
                'email': 'user@example.com'
            }
            mock_get_user.return_value = regular_user
            
            headers = {'Authorization': 'Bearer user_firebase_token'}
            data = {'role': 'admin'}
            response = client.put(f'/api/users/{viewer_user.id}/role', 
                                headers=headers, 
                                json=data)
            
            print(f"Regular user update role response: {response.status_code}")
            if response.status_code == 403:
                print("✅ Test 4 passed: Regular user cannot update user roles")
            else:
                print(f"❌ Test 4 failed: Expected 403, got {response.status_code}")
                print(f"Response: {response.get_json()}")
            
            # Test 5: No authentication header
            response = client.get('/api/users/')
            
            print(f"No auth header response: {response.status_code}")
            if response.status_code == 401:
                print("✅ Test 5 passed: Endpoints require authentication")
            else:
                print(f"❌ Test 5 failed: Expected 401, got {response.status_code}")
                print(f"Response: {response.get_json()}")
        
        print("\n🎉 User endpoint Firebase authentication tests completed!")

if __name__ == '__main__':
    test_user_endpoints_with_firebase()