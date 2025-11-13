"""
Unit tests for Firebase Authentication components
Tests the FirebaseAuthManager, decorators, and authentication flow
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import the components to test
from app.middleware.firebase_auth import (
    FirebaseAuthManager, 
    require_firebase_auth, 
    verify_firebase_token,
    validate_firebase_startup_config,
    get_firebase_config_summary
)
from app.models.production.user_models import User
from app.models.production.permissions import UserRole


class TestFirebaseAuthManager:
    """Test cases for FirebaseAuthManager class"""
    
    @pytest.fixture
    def auth_manager(self):
        """Create a FirebaseAuthManager instance for testing"""
        with patch('app.middleware.firebase_auth.firebase_admin'):
            manager = FirebaseAuthManager()
            return manager
    
    @pytest.fixture
    def mock_firebase_token(self):
        """Mock Firebase token data"""
        return {
            'uid': 'test_firebase_uid_123',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/avatar.jpg',
            'email_verified': True,
            'auth_time': 1640995200,
            'firebase': {
                'sign_in_provider': 'google.com'
            }
        }
    
    def test_initialization_with_service_account_file(self, auth_manager):
        """Test Firebase initialization with service account file"""
        with patch.dict(os.environ, {
            'FIREBASE_SERVICE_ACCOUNT_PATH': 'test/path/service-account.json'
        }):
            with patch('os.path.exists', return_value=True):
                with patch('os.access', return_value=True):
                    with patch('builtins.open', mock_open_json({'type': 'service_account', 'project_id': 'test'})):
                        with patch('app.middleware.firebase_auth.credentials.Certificate'):
                            with patch('app.middleware.firebase_auth.firebase_admin.initialize_app'):
                                result = auth_manager._try_service_account_file()
                                assert result is True
    
    def test_initialization_with_environment_variables(self, auth_manager):
        """Test Firebase initialization with environment variables"""
        with patch.dict(os.environ, {
            'FIREBASE_PROJECT_ID': 'test-project',
            'FIREBASE_PRIVATE_KEY': '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n',
            'FIREBASE_CLIENT_EMAIL': 'test@test-project.iam.gserviceaccount.com'
        }):
            with patch('app.middleware.firebase_auth.credentials.Certificate'):
                with patch('app.middleware.firebase_auth.firebase_admin.initialize_app'):
                    result = auth_manager._try_environment_variables()
                    assert result is True
    
    def test_verify_token_success(self, auth_manager, mock_firebase_token):
        """Test successful token verification"""
        auth_manager._initialized = True
        
        with patch('app.middleware.firebase_auth.auth.verify_id_token', return_value=mock_firebase_token):
            result = auth_manager.verify_token('valid_token')
            assert result == mock_firebase_token
    
    def test_verify_token_not_initialized(self, auth_manager):
        """Test token verification when Firebase not initialized"""
        auth_manager._initialized = False
        
        result = auth_manager.verify_token('any_token')
        assert result is None
    
    def test_verify_token_invalid(self, auth_manager):
        """Test token verification with invalid token"""
        auth_manager._initialized = True
        
        with patch('app.middleware.firebase_auth.auth.verify_id_token', side_effect=Exception('Invalid token')):
            result = auth_manager.verify_token('invalid_token')
            assert result is None
    
    def test_get_or_create_user_existing_by_firebase_uid(self, auth_manager, mock_firebase_token, app, db):
        """Test getting existing user by Firebase UID"""
        with app.app_context():
            # Create existing user
            existing_user = User(
                firebase_uid='test_firebase_uid_123',
                email='test@example.com',
                username='testuser',
                is_active=True,
                role=UserRole.USER
            )
            db.session.add(existing_user)
            db.session.commit()
            
            result = auth_manager.get_or_create_user(mock_firebase_token)
            
            assert result is not None
            assert result.firebase_uid == 'test_firebase_uid_123'
            assert result.email == 'test@example.com'
            assert result.last_login is not None
    
    def test_get_or_create_user_existing_by_email(self, auth_manager, mock_firebase_token, app, db):
        """Test linking existing user by email to Firebase"""
        with app.app_context():
            # Create existing user without Firebase UID
            existing_user = User(
                email='test@example.com',
                username='testuser',
                is_active=True,
                role=UserRole.USER
            )
            db.session.add(existing_user)
            db.session.commit()
            
            result = auth_manager.get_or_create_user(mock_firebase_token)
            
            assert result is not None
            assert result.firebase_uid == 'test_firebase_uid_123'
            assert result.email == 'test@example.com'
    
    def test_get_or_create_user_new_user(self, auth_manager, mock_firebase_token, app, db):
        """Test creating new user from Firebase token"""
        with app.app_context():
            result = auth_manager.get_or_create_user(mock_firebase_token)
            
            assert result is not None
            assert result.firebase_uid == 'test_firebase_uid_123'
            assert result.email == 'test@example.com'
            assert result.first_name == 'Test'
            assert result.last_name == 'User'
            assert result.username == 'test'
            assert result.is_active is True
            assert result.role == UserRole.USER
    
    def test_get_or_create_user_missing_required_fields(self, auth_manager):
        """Test user creation with missing required fields"""
        invalid_token = {'uid': 'test_uid'}  # Missing email
        
        result = auth_manager.get_or_create_user(invalid_token)
        assert result is None
    
    def test_validate_configuration_valid_service_account(self, auth_manager):
        """Test configuration validation with valid service account file"""
        with patch.dict(os.environ, {
            'FIREBASE_SERVICE_ACCOUNT_PATH': 'test/service-account.json'
        }):
            with patch.object(auth_manager, '_validate_service_account_file', return_value={
                'valid': True,
                'errors': [],
                'project_id': 'test-project'
            }):
                result = auth_manager.validate_configuration()
                assert result['valid'] is True
    
    def test_validate_configuration_valid_env_vars(self, auth_manager):
        """Test configuration validation with valid environment variables"""
        with patch.dict(os.environ, {
            'FIREBASE_PROJECT_ID': 'test-project',
            'FIREBASE_PRIVATE_KEY': '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n',
            'FIREBASE_CLIENT_EMAIL': 'test@test-project.iam.gserviceaccount.com'
        }):
            with patch.object(auth_manager, '_validate_environment_variables', return_value={
                'valid': True,
                'warnings': [],
                'project_id': 'test-project'
            }):
                result = auth_manager.validate_configuration()
                assert result['valid'] is True
    
    def test_force_reinitialize(self, auth_manager):
        """Test force reinitialization"""
        auth_manager._initialized = True
        auth_manager._app = Mock()
        
        with patch('app.middleware.firebase_auth.firebase_admin.delete_app'):
            with patch.object(auth_manager, '_initialize_firebase', return_value=True):
                result = auth_manager.force_reinitialize()
                assert result is True
                assert auth_manager._initialized is False
                assert auth_manager._initialization_attempts == 0


class TestAuthenticationDecorators:
    """Test cases for authentication decorators"""
    
    @pytest.fixture
    def mock_request(self):
        """Mock Flask request object"""
        request = Mock()
        request.headers = {}
        request.method = 'GET'
        request.endpoint = 'test_endpoint'
        request.path = '/test'
        return request
    
    @pytest.fixture
    def mock_firebase_user(self):
        """Mock Firebase user object"""
        user = Mock()
        user.id = 1
        user.email = 'test@example.com'
        user.firebase_uid = 'test_uid'
        return user
    
    def test_require_firebase_auth_no_header(self, app, mock_request):
        """Test require_firebase_auth decorator without Authorization header"""
        with app.test_request_context():
            with patch('app.middleware.firebase_auth.request', mock_request):
                @require_firebase_auth
                def test_view():
                    return "success"
                
                response, status_code = test_view()
                assert status_code == 401
                assert 'MISSING_AUTH_HEADER' in response.get_json()['code']
    
    def test_require_firebase_auth_invalid_header_format(self, app, mock_request):
        """Test require_firebase_auth decorator with invalid header format"""
        mock_request.headers = {'Authorization': 'InvalidFormat token'}
        
        with app.test_request_context():
            with patch('app.middleware.firebase_auth.request', mock_request):
                @require_firebase_auth
                def test_view():
                    return "success"
                
                response, status_code = test_view()
                assert status_code == 401
                assert 'INVALID_AUTH_HEADER' in response.get_json()['code']
    
    def test_require_firebase_auth_firebase_not_initialized(self, app, mock_request):
        """Test require_firebase_auth decorator when Firebase not initialized"""
        mock_request.headers = {'Authorization': 'Bearer valid_token'}
        
        with app.test_request_context():
            with patch('app.middleware.firebase_auth.request', mock_request):
                with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', False):
                    @require_firebase_auth
                    def test_view():
                        return "success"
                    
                    response, status_code = test_view()
                    assert status_code == 503
                    assert 'AUTH_SERVICE_UNAVAILABLE' in response.get_json()['code']
    
    def test_require_firebase_auth_invalid_token(self, app, mock_request):
        """Test require_firebase_auth decorator with invalid token"""
        mock_request.headers = {'Authorization': 'Bearer invalid_token'}
        
        with app.test_request_context():
            with patch('app.middleware.firebase_auth.request', mock_request):
                with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
                    with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=None):
                        @require_firebase_auth
                        def test_view():
                            return "success"
                        
                        response, status_code = test_view()
                        assert status_code == 401
                        assert 'INVALID_TOKEN' in response.get_json()['code']
    
    def test_require_firebase_auth_success(self, app, mock_request, mock_firebase_user):
        """Test successful authentication with require_firebase_auth decorator"""
        mock_request.headers = {'Authorization': 'Bearer valid_token'}
        mock_token = {'uid': 'test_uid', 'email': 'test@example.com'}
        
        with app.test_request_context():
            with patch('app.middleware.firebase_auth.request', mock_request):
                with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
                    with patch('app.middleware.firebase_auth.firebase_auth_manager.verify_token', return_value=mock_token):
                        with patch('app.middleware.firebase_auth.firebase_auth_manager.get_or_create_user', return_value=mock_firebase_user):
                            with patch('app.middleware.firebase_auth.g') as mock_g:
                                @require_firebase_auth
                                def test_view():
                                    return "success"
                                
                                result = test_view()
                                assert result == "success"
                                assert mock_g.firebase_token == mock_token
                                assert mock_g.current_user == mock_firebase_user


class TestConfigurationValidation:
    """Test cases for configuration validation functions"""
    
    def test_validate_firebase_startup_config_success(self):
        """Test successful startup configuration validation"""
        with patch('app.middleware.firebase_auth.firebase_auth_manager.validate_configuration', return_value={
            'valid': True,
            'errors': [],
            'warnings': [],
            'service_account_file': {'valid': True, 'project_id': 'test-project'},
            'recommendations': []
        }):
            result = validate_firebase_startup_config()
            assert result is True
    
    def test_validate_firebase_startup_config_failure(self):
        """Test failed startup configuration validation"""
        with patch('app.middleware.firebase_auth.firebase_auth_manager.validate_configuration', return_value={
            'valid': False,
            'errors': ['Missing service account file'],
            'warnings': ['No environment variables set'],
            'recommendations': ['Set FIREBASE_SERVICE_ACCOUNT_PATH']
        }):
            result = validate_firebase_startup_config()
            assert result is False
    
    def test_get_firebase_config_summary(self):
        """Test Firebase configuration summary"""
        with patch('app.middleware.firebase_auth.firebase_auth_manager._initialized', True):
            with patch('app.middleware.firebase_auth.firebase_auth_manager.validate_configuration', return_value={'valid': True}):
                with patch.dict(os.environ, {
                    'FIREBASE_PROJECT_ID': 'test-project',
                    'FIREBASE_SERVICE_ACCOUNT_PATH': 'test/path'
                }):
                    result = get_firebase_config_summary()
                    
                    assert 'initialized' in result
                    assert 'validation_result' in result
                    assert 'environment_summary' in result
                    assert result['environment_summary']['project_id'] == 'test-project'


def mock_open_json(data):
    """Helper function to mock open() for JSON files"""
    import io
    return io.StringIO(json.dumps(data))


# Pytest fixtures for Flask app and database
@pytest.fixture
def app():
    """Create Flask app for testing"""
    from app import create_app, db
    
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def db(app):
    """Create database for testing"""
    from app import db as _db
    
    with app.app_context():
        yield _db


if __name__ == '__main__':
    pytest.main([__file__, '-v'])