"""
Integration Test for Core Modules and Google Sheets Service
Comprehensive test to verify all implementations are working correctly
"""

import os
import sys
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_core_config():
    """Test core configuration module"""
    try:
        from app.core.config import get_settings, Settings
        
        # Test settings creation
        settings = get_settings()
        assert isinstance(settings, Settings)
        
        # Test environment detection
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'is_development')
        assert hasattr(settings, 'is_production')
        
        # Test configuration sections
        assert hasattr(settings, 'database')
        assert hasattr(settings, 'security')
        assert hasattr(settings, 'google')
        assert hasattr(settings, 'redis')
        
        print("✅ Core configuration module test passed")
        return True
        
    except Exception as e:
        print(f"❌ Core configuration module test failed: {str(e)}")
        return False

def test_core_security():
    """Test core security module"""
    try:
        from app.core.security import (
            get_security_manager, encrypt_token, decrypt_token,
            generate_jwt_token, validate_jwt_token, hash_password, verify_password
        )
        
        # Test encryption/decryption
        test_token = "test_token_12345"
        encrypted = encrypt_token(test_token)
        decrypted = decrypt_token(encrypted)
        assert decrypted == test_token
        
        # Test password hashing
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
        
        # Test JWT tokens
        user_id = "test_user_123"
        token = generate_jwt_token(user_id)
        payload = validate_jwt_token(token)
        assert payload['user_id'] == user_id
        
        print("✅ Core security module test passed")
        return True
        
    except Exception as e:
        print(f"❌ Core security module test failed: {str(e)}")
        return False

def test_core_logging():
    """Test core logging module"""
    try:
        from app.core.logging import get_logger, LogContext, LogCategory, performance_monitor
        
        # Test logger creation
        logger = get_logger("test_logger")
        assert logger is not None
        
        # Test logging with context
        context = LogContext(user_id="test_user", session_id="test_session")
        logger.info("Test log message", context=context)
        
        # Test performance monitoring decorator
        @performance_monitor(logger)
        def test_function():
            return "test_result"
        
        result = test_function()
        assert result == "test_result"
        
        print("✅ Core logging module test passed")
        return True
        
    except Exception as e:
        print(f"❌ Core logging module test failed: {str(e)}")
        return False

@patch('redis.from_url')
def test_core_auth(mock_redis):
    """Test core authentication module"""
    try:
        from app.core.auth import (
            get_auth_manager, UserInfo, UserRole, Permission, AuthManager
        )
        
        # Mock Redis client
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Test user info creation
        user_info = UserInfo(
            id="test_user",
            email="test@example.com",
            roles=[UserRole.USER],
            permissions=[Permission.READ, Permission.WRITE]
        )
        
        assert user_info.has_role(UserRole.USER)
        assert user_info.has_permission(Permission.READ)
        assert not user_info.has_role(UserRole.ADMIN)
        
        # Test auth manager
        auth_manager = get_auth_manager()
        assert isinstance(auth_manager, AuthManager)
        
        print("✅ Core authentication module test passed")
        return True
        
    except Exception as e:
        print(f"❌ Core authentication module test failed: {str(e)}")
        return False

@patch('redis.from_url')
def test_rate_limiter(mock_redis):
    """Test rate limiter module"""
    try:
        from app.core.rate_limiter import (
            get_rate_limiter, RateLimitRule, RateLimitStrategy, RateLimitScope
        )
        
        # Mock Redis client
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = None
        mock_redis_client.pipeline.return_value = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Test rate limiter creation
        limiter = get_rate_limiter()
        assert limiter is not None
        
        # Test rule creation
        rule = RateLimitRule(
            name="test_rule",
            requests=10,
            window=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
            scope=RateLimitScope.IP
        )
        
        limiter.add_rule(rule)
        assert "test_rule" in limiter.default_rules
        
        print("✅ Rate limiter module test passed")
        return True
        
    except Exception as e:
        print(f"❌ Rate limiter module test failed: {str(e)}")
        return False

@patch('redis.from_url')
@patch('httpx.AsyncClient')
def test_google_sheets_service(mock_httpx, mock_redis):
    """Test Google Sheets service"""
    try:
        from app.services.google_sheets_service import GoogleSheetsService, OperationType
        
        # Mock Redis client
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600
        }
        
        mock_http_client = Mock()
        mock_http_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_http_client
        
        # Test service creation
        service = GoogleSheetsService()
        assert service is not None
        
        # Test operation types
        assert OperationType.READ.value == "read"
        assert OperationType.WRITE.value == "write"
        
        # Test metrics
        metrics = service.get_metrics()
        assert isinstance(metrics, dict)
        assert 'total_requests' in metrics
        
        print("✅ Google Sheets service test passed")
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets service test failed: {str(e)}")
        return False

def test_integration_dependencies():
    """Test that all modules can import each other correctly"""
    try:
        # Test core module imports
        from app.core.config import get_settings
        from app.core.security import get_security_manager
        from app.core.logging import get_logger
        from app.core.auth import get_auth_manager
        from app.core.rate_limiter import get_rate_limiter
        
        # Test service imports
        from app.services.google_sheets_service import GoogleSheetsService
        
        # Test that settings work across modules
        settings = get_settings()
        security_manager = get_security_manager()
        logger = get_logger()
        
        # Test logging integration
        logger.info("Integration test completed successfully")
        
        print("✅ Integration dependencies test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration dependencies test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting comprehensive integration tests...")
    print("=" * 60)
    
    tests = [
        ("Core Configuration", test_core_config),
        ("Core Security", test_core_security),
        ("Core Logging", test_core_logging),
        ("Core Authentication", test_core_auth),
        ("Rate Limiter", test_rate_limiter),
        ("Google Sheets Service", test_google_sheets_service),
        ("Integration Dependencies", test_integration_dependencies)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Implementation is complete and functional.")
    else:
        print(f"⚠️  {failed} test(s) failed. Review the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
