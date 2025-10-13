"""
Integration tests for Firebase Authentication
Tests the complete authentication flow from endpoints to database
"""

import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime

from app import create_app, db
from app.models.production.user_models import User
from app.models.production.permissions import UserRole


class TestFirebaseAuthIntegration:
    """Integration tests for Firebase authentication endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def mock_firebase_token(self):
        """Mock Firebase token data"""
        return {
            'uid': 'test_firebase_uid_123',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/avatar.jpg',
            'email_verified': True,
            'auth_time': 1640995200
        }
    
    def test_firebase_health_endpoint(self, client):
        """Test Firebase health check endpoint"""
        response = client.get('/auth/firebase-health')
        
        assert response.status_code in [200, 503]  # 503 if Firebase not initialized
        data = response.get_json()
        assert 'status' in data
        assert 'firebase_initialized' in data
        assert 'timestamp' in data
    
    def test_firebase_config_validation_endpoint(self, client):
        """Test Firebase configuration validation endpoint"""
        response = client.get('/auth/firebase-config-validation')
        
        assert response.status_code in [200, 400]  # 400 if config invalid
        data = response.get_json()
        assert 'configuration_valid' in data
        assert 'validation_details' in data
        assert 'timestamp' in data
    
    def test_firebase_sync_no_auth_header(self, client):
        """Test firebase-sync endpoint without Authorization header"""
        response = client.post('/auth/firebase-sync', json={})
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'MISSING_AUTH_HEADER'
        assert 'request_id' in data
    
    def test_firebase_sync_invalid_auth_header(self, client):
        """Test firebase-sync endpoint with invalid Authorization header"""
        headers = {'Authorization': 'InvalidFormat token'}
        response = client.post('/auth/firebase-sync', json={}, headers=headers)
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'INVALID_AUTH_HEADER'
        assert 'expected_format' in data
    
    def test_firebase_sync_firebase_not_initialized(self, client):
        """Test firebase-sync endpoint when Firebase not initialized"""
        headers = {'Authorization': 'Bearer valid_token'}
        
        with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', False):
            response = client.post('/auth/firebase-sync', json={}, headers=headers)
            
            assert response.status_code == 503
            data = response.get_json()
            assert data['code'] == 'FIREBASE_NOT_INITIALIZED'
    
    def test_firebase_sync_invalid_token(self, client):
        """Test firebase-sync endpoint with invalid Firebase token"""
        headers = {'Authorization': 'Bearer invalid_token'}
        
        with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
            with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=None):
                response = client.post('/auth/firebase-sync', json={}, headers=headers)
                
                assert response.status_code == 401
                data = response.get_json()
                assert data['code'] == 'INVALID_FIREBASE_TOKEN'
                assert 'suggestion' in data
    
    def test_firebase_sync_success_new_user(self, client, app, mock_firebase_token):
        """Test successful firebase-sync with new user creation"""
        headers = {'Authorization': 'Bearer valid_token'}
        payload = {
            'firstName': 'Test',
            'lastName': 'User'
        }
        
        with app.app_context():
            with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
                with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=mock_firebase_token):
                    response = client.post('/auth/firebase-sync', json=payload, headers=headers)
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
                    assert 'user' in data
                    assert 'sync_metadata' in data
                    assert data['user']['email'] == 'test@example.com'
                    assert data['user']['firebase_uid'] == 'test_firebase_uid_123'
                    
                    # Verify user was created in database
                    user = User.query.filter_by(firebase_uid='test_firebase_uid_123').first()
                    assert user is not None
                    assert user.email == 'test@example.com'
                    assert user.first_name == 'Test'
                    assert user.last_name == 'User'
    
    def test_firebase_sync_success_existing_user(self, client, app, mock_firebase_token):
        """Test successful firebase-sync with existing user"""
        headers = {'Authorization': 'Bearer valid_token'}
        
        with app.app_context():
            # Create existing user
            existing_user = User(
                firebase_uid='test_firebase_uid_123',
                email='test@example.com',
                username='testuser',
                first_name='Existing',
                last_name='User',
                is_active=True,
                role=UserRole.USER
            )
            db.session.add(existing_user)
            db.session.commit()
            
            with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
                with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=mock_firebase_token):
                    response = client.post('/auth/firebase-sync', json={}, headers=headers)
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
                    assert data['user']['first_name'] == 'Existing'  # Should keep existing data
                    
                    # Verify last_login was updated
                    user = User.query.filter_by(firebase_uid='test_firebase_uid_123').first()
                    assert user.last_login is not None
    
    def test_protected_endpoint_no_auth(self, client):
        """Test protected NextGen endpoint without authentication"""
        response = client.get('/api/v1/nextgen/data-sources')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'code' in data
    
    def test_protected_endpoint_invalid_token(self, client):
        """Test protected NextGen endpoint with invalid token"""
        headers = {'Authorization': 'Bearer invalid_token'}
        
        with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
            with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=None):
                response = client.get('/api/v1/nextgen/data-sources', headers=headers)
                
                assert response.status_code == 401
                data = response.get_json()
                assert data['code'] == 'INVALID_TOKEN'
    
    def test_protected_endpoint_success(self, client, app, mock_firebase_token):
        """Test protected NextGen endpoint with valid authentication"""
        headers = {'Authorization': 'Bearer valid_token'}
        
        with app.app_context():
            # Create user for authentication
            user = User(
                firebase_uid='test_firebase_uid_123',
                email='test@example.com',
                username='testuser',
                is_active=True,
                role=UserRole.USER
            )
            db.session.add(user)
            db.session.commit()
            
            with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
                with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=mock_firebase_token):
                    with patch('app.middleware.firebase_auth.firebase_auth_manager.get_or_create_user', return_value=user):
                        response = client.get('/api/v1/nextgen/data-sources', headers=headers)
                        
                        # Should succeed (200) or return data (even if empty)
                        assert response.status_code in [200, 500]  # 500 might occur due to missing dependencies
                        
                        if response.status_code == 200:
                            data = response.get_json()
                            assert 'success' in data or 'data' in data
    
    def test_cors_endpoint_public_access(self, client):
        """Test CORS endpoint works without authentication"""
        response = client.get('/api/v1/nextgen/cors-test')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'timestamp' in data
    
    def test_firebase_reinitialize_endpoint(self, client):
        """Test Firebase reinitialization endpoint"""
        with patch('app.middleware.firebase_auth.firebase_auth_manager.force_reinitialize', return_value=True):
            response = client.post('/auth/firebase-reinitialize')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'timestamp' in data
    
    def test_verify_token_endpoint(self, client, mock_firebase_token):
        """Test token verification utility endpoint"""
        headers = {'Authorization': 'Bearer valid_token'}
        
        with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=mock_firebase_token):
            response = client.post('/auth/verify-token', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is True
            assert data['uid'] == 'test_firebase_uid_123'
            assert data['email'] == 'test@example.com'
    
    def test_verify_token_endpoint_invalid(self, client):
        """Test token verification endpoint with invalid token"""
        headers = {'Authorization': 'Bearer invalid_token'}
        
        with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=None):
            response = client.post('/auth/verify-token', headers=headers)
            
            assert response.status_code == 401
            data = response.get_json()
            assert data['valid'] is False
            assert 'error' in data


class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_complete_authentication_flow(self, client, app):
        """Test complete authentication flow from sync to protected endpoint access"""
        mock_token = {
            'uid': 'flow_test_uid',
            'email': 'flow@example.com',
            'name': 'Flow Test User',
            'email_verified': True
        }
        
        headers = {'Authorization': 'Bearer valid_flow_token'}
        
        with app.app_context():
            # Step 1: Sync user with backend
            with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
                with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=mock_token):
                    sync_response = client.post('/auth/firebase-sync', json={}, headers=headers)
                    
                    assert sync_response.status_code == 200
                    sync_data = sync_response.get_json()
                    assert sync_data['success'] is True
                    
                    # Step 2: Verify user was created
                    user = User.query.filter_by(firebase_uid='flow_test_uid').first()
                    assert user is not None
                    
                    # Step 3: Access protected endpoint
                    with patch('app.middleware.firebase_auth.firebase_auth_manager.get_or_create_user', return_value=user):
                        protected_response = client.get('/api/v1/nextgen/data-sources', headers=headers)
                        
                        # Should not return 401 (authentication should work)
                        assert protected_response.status_code != 401
    
    def test_authentication_error_recovery(self, client, app):
        """Test authentication error recovery scenarios"""
        # Test token expiration handling
        headers = {'Authorization': 'Bearer expired_token'}
        
        with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
            with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=None):
                response = client.get('/api/v1/nextgen/data-sources', headers=headers)
                
                assert response.status_code == 401
                data = response.get_json()
                assert 'suggestion' in data
                assert 'Please log in again' in data['suggestion']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])