"""
Simple test for get_current_firebase_user function
Tests for task 2.1: Test get_current_firebase_user function
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from flask import Flask, g
from datetime import datetime

# Create a minimal Flask app for testing
app = Flask(__name__)
app.config['TESTING'] = True

def test_get_current_firebase_user():
    """Test get_current_firebase_user function"""
    
    # Import the function we want to test
    from app.middleware.firebase_auth import get_current_firebase_user
    from app.models.production.user_models import User
    from app.models.production.permissions import UserRole
    
    print("Testing get_current_firebase_user function...")
    
    with app.test_request_context():
        # Test 1: No user in g - should return None
        if hasattr(g, 'current_user'):
            delattr(g, 'current_user')
        
        result = get_current_firebase_user()
        assert result is None, "Expected None when no user in g"
        print("✅ Test 1 passed: Returns None when no user in g")
        
        # Test 2: User in g - should return the user
        mock_user = User(
            id=1,
            email='test@example.com',
            firebase_uid='test_uid_123',
            first_name='Test',
            last_name='User',
            role=UserRole.USER
        )
        
        g.current_user = mock_user
        result = get_current_firebase_user()
        
        assert result is not None, "Expected user object when user in g"
        assert result.email == 'test@example.com', "Expected correct email"
        assert result.firebase_uid == 'test_uid_123', "Expected correct Firebase UID"
        assert result.role == UserRole.USER, "Expected correct role"
        print("✅ Test 2 passed: Returns user when stored in g")
        
        # Test 3: Complete user with all fields
        complete_user = User(
            id=2,
            email='complete@example.com',
            firebase_uid='complete_uid_456',
            username='complete_user',
            first_name='Complete',
            last_name='User',
            phone='+1234567890',
            company='Test Company',
            job_title='Developer',
            bio='Test bio',
            avatar_url='https://example.com/avatar.jpg',
            is_active=True,
            role=UserRole.ADMIN,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        g.current_user = complete_user
        result = get_current_firebase_user()
        
        # Verify all required fields are present
        assert result is not None, "Expected user object"
        assert result.id == 2, "Expected correct ID"
        assert result.email == 'complete@example.com', "Expected correct email"
        assert result.firebase_uid == 'complete_uid_456', "Expected correct Firebase UID"
        assert result.username == 'complete_user', "Expected correct username"
        assert result.first_name == 'Complete', "Expected correct first name"
        assert result.last_name == 'User', "Expected correct last name"
        assert result.phone == '+1234567890', "Expected correct phone"
        assert result.company == 'Test Company', "Expected correct company"
        assert result.job_title == 'Developer', "Expected correct job title"
        assert result.bio == 'Test bio', "Expected correct bio"
        assert result.avatar_url == 'https://example.com/avatar.jpg', "Expected correct avatar URL"
        assert result.is_active is True, "Expected user to be active"
        assert result.role == UserRole.ADMIN, "Expected correct role"
        assert result.created_at is not None, "Expected created_at timestamp"
        assert result.updated_at is not None, "Expected updated_at timestamp"
        assert result.last_login is not None, "Expected last_login timestamp"
        
        # Test User model methods
        assert result.get_full_name() == 'Complete User', "Expected correct full name"
        assert hasattr(result, 'has_permission'), "Expected has_permission method"
        assert hasattr(result, 'to_dict'), "Expected to_dict method"
        print("✅ Test 3 passed: Returns User model instance with all required fields")
        
        print("\n🎉 All tests passed! get_current_firebase_user function works correctly.")

if __name__ == '__main__':
    test_get_current_firebase_user()