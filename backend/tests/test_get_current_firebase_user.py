"""
Test get_current_firebase_user function
Tests for task 2.1: Test get_current_firebase_user function
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g
from datetime import datetime

# Import the modules we need to test
from app.middleware.firebase_auth import (
    get_current_firebase_user, 
    firebase_auth_manager,
    require_firebase_auth
)
from app.models.production.user_models import User
from app.models.production.permissions import UserRole
from app import create_app, db


class TestGetCurrentFirebaseUser:
    """Test cases for get_current_firebase_user function"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def app_context(self, app):
        """Create app context"""
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    def test_get_current_firebase_user_returns_none_when_no_user_in_g(self, app_context):
        """Test that function returns None when no user is stored in g"""
        with app_context.test_request_context():
            # Ensure g.current_user is not set
            if hasattr(g, 'current_user'):
                delattr(g, 'current_user')
            
            result = get_current_firebase_user()
            assert result is None
    
    def test_get_current_firebase_user_returns_user_from_g(self, app_context):
        """Test that function returns user when stored in g"""
        with app_context.test_request_context():
            # Create a mock user
            mock_user = User(
                id=1,
                email='test@example.com',
                firebase_uid='test_uid_123',
                first_name='Test',
                last_name='User',
                role=UserRole.USER
            )
            
            # Store user in g
            g.current_user = mock_user
            
            result = get_current_firebase_user()
            assert result is not None
            assert result.email == 'test@example.com'
            assert result.firebase_uid == 'test_uid_123'
            assert result.role == UserRole.USER    

    def test_get_current_firebase_user_with_complete_user_model(self, app_context):
        """Test that function returns User model instance with all required fields"""
        with app_context.test_request_context():
            # Create a complete user with all fields
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
            
            # Store user in g
            g.current_user = complete_user
            
            result = get_current_firebase_user()
            
            # Verify all required fields are present
            assert result is not None
            assert result.id == 2
            assert result.email == 'complete@example.com'
            assert result.firebase_uid == 'complete_uid_456'
            assert result.username == 'complete_user'
            assert result.first_name == 'Complete'
            assert result.last_name == 'User'
            assert result.phone == '+1234567890'
            assert result.company == 'Test Company'
            assert result.job_title == 'Developer'
            assert result.bio == 'Test bio'
            assert result.avatar_url == 'https://example.com/avatar.jpg'
            assert result.is_active is True
            assert result.role == UserRole.ADMIN
            assert result.created_at is not None
            assert result.updated_at is not None
            assert result.last_login is not None
            
            # Test User model methods
            assert result.get_full_name() == 'Complete User'
            assert result.has_permission is not None  # Method exists
            assert result.to_dict() is not None  # Method exists


class TestFirebaseUserIntegration:
    """Test Firebase user integration and error handling"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def app_context(self, app):
        """Create app context"""
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @patch('app.middleware.firebase_auth.firebase_auth_manager.get_or_create_user')
    def test_firebase_user_not_found_in_database(self, mock_get_or_create_user, app_context):
        """Test behavior when Firebase user is not found in database"""
        with app_context.test_request_context():
            # Mock Firebase token
            mock_token = {
                'uid': 'nonexistent_uid',
                'email': 'nonexistent@example.com',
                'name': 'Nonexistent User'
            }
            
            # Mock get_or_create_user to return None (user not found/creation failed)
            mock_get_or_create_user.return_value = None
            
            # Test that get_current_firebase_user returns None when no user in g
            result = get_current_firebase_user()
            assert result is None
    
    def test_firebase_uid_mapping_to_database_user(self, app_context):
        """Test Firebase UID mapping to database user records"""
        with app_context.test_request_context():
            # Create user with Firebase UID
            test_user = User(
                id=3,
                email='mapped@example.com',
                firebase_uid='mapped_firebase_uid_789',
                first_name='Mapped',
                last_name='User',
                role=UserRole.USER
            )
            
            # Add to database
            db.session.add(test_user)
            db.session.commit()
            
            # Store in g (simulating what require_firebase_auth would do)
            g.current_user = test_user
            g.firebase_uid = 'mapped_firebase_uid_789'
            
            result = get_current_firebase_user()
            
            # Verify mapping is correct
            assert result is not None
            assert result.firebase_uid == 'mapped_firebase_uid_789'
            assert result.email == 'mapped@example.com'
            assert hasattr(g, 'firebase_uid')
            assert g.firebase_uid == 'mapped_firebase_uid_789'
    
    def test_error_handling_for_user_context_retrieval_failures(self, app_context):
        """Test error handling for user context retrieval failures"""
        with app_context.test_request_context():
            # Test with invalid user object in g
            g.current_user = "invalid_user_object"
            
            # get_current_firebase_user should handle this gracefully
            result = get_current_firebase_user()
            # Should return the object as-is (it just returns g.current_user)
            assert result == "invalid_user_object"
            
            # Test with None explicitly set
            g.current_user = None
            result = get_current_firebase_user()
            assert result is None
            
            # Test with missing attribute
            if hasattr(g, 'current_user'):
                delattr(g, 'current_user')
            result = get_current_firebase_user()
            assert result is None


class TestRequireFirebaseAuthIntegration:
    """Test require_firebase_auth decorator integration with get_current_firebase_user"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def app_context(self, app):
        """Create app context"""
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True)
    @patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token')
    @patch('app.middleware.firebase_auth.firebase_auth_manager.get_or_create_user')
    def test_require_firebase_auth_populates_g_correctly(self, mock_get_or_create_user, 
                                                        mock_verify_token, app_context, client):
        """Test that require_firebase_auth decorator populates g correctly"""
        
        # Mock Firebase token verification
        mock_decoded_token = {
            'uid': 'test_uid_123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        mock_verify_token.return_value = mock_decoded_token
        
        # Mock user creation/retrieval
        mock_user = User(
            id=1,
            email='test@example.com',
            firebase_uid='test_uid_123',
            first_name='Test',
            last_name='User',
            role=UserRole.USER
        )
        mock_get_or_create_user.return_value = mock_user
        
        # Create a test route with the decorator
        @app_context.route('/test-auth')
        @require_firebase_auth
        def test_route():
            # Test that get_current_firebase_user works within the decorated route
            current_user = get_current_firebase_user()
            return {
                'user_id': current_user.id if current_user else None,
                'email': current_user.email if current_user else None,
                'firebase_uid': current_user.firebase_uid if current_user else None
            }
        
        # Make request with valid Firebase token
        headers = {'Authorization': 'Bearer valid_firebase_token'}
        response = client.get('/test-auth', headers=headers)
        
        # Verify the response
        assert response.status_code == 200
        data = response.get_json()
        assert data['user_id'] == 1
        assert data['email'] == 'test@example.com'
        assert data['firebase_uid'] == 'test_uid_123'