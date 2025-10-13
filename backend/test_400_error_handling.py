#!/usr/bin/env python3
"""
Comprehensive test suite for HTTP 400 error handling improvements
Tests the standardized error response format and validation across the API
"""

import json
import pytest
import tempfile
import os
from flask import Flask
from app import create_app, db
from app.validation.decorators import ErrorHandler, ValidationError
from app.validation.schemas import ValidationUtils


class Test400ErrorHandling:
    """Test suite for HTTP 400 error handling"""

    @pytest.fixture
    def app(self):
        """Create test application"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def app_context(self, app):
        """Create application context"""
        with app.app_context():
            yield app

    def test_error_handler_format_error_response(self, app_context):
        """Test ErrorHandler.format_error_response format"""
        with app_context.test_request_context():
            response, status_code = ErrorHandler.format_error_response(
                message="Test error message",
                code="TEST_ERROR",
                details={"field": "test_field", "value": "invalid_value"}
            )

            response_data = json.loads(response.get_data(as_text=True))

            # Check response structure
            assert response_data['success'] is False
            assert response_data['error'] is True
            assert response_data['message'] == "Test error message"
            assert response_data['code'] == "TEST_ERROR"
            assert response_data['details']['field'] == "test_field"
            assert 'timestamp' in response_data
            assert 'request_id' in response_data
            assert status_code == 400

    def test_error_handler_validation_error(self, app_context):
        """Test ErrorHandler.validation_error format"""
        with app_context.test_request_context():
            errors = {
                'email': ['Invalid email format'],
                'password': ['Password too short', 'Missing special character']
            }

            response, status_code = ErrorHandler.validation_error(errors)
            response_data = json.loads(response.get_data(as_text=True))

            assert response_data['code'] == 'VALIDATION_ERROR'
            assert response_data['details']['field_errors'] == errors
            assert response_data['details']['total_errors'] == 2
            assert status_code == 400

    def test_error_handler_bad_request_error(self, app_context):
        """Test ErrorHandler.bad_request_error format"""
        with app_context.test_request_context():
            missing_fields = ['template_id', 'data_source']
            invalid_fields = {'formats': 'Must be an array'}

            response, status_code = ErrorHandler.bad_request_error(
                message="Request validation failed",
                missing_fields=missing_fields,
                invalid_fields=invalid_fields
            )

            response_data = json.loads(response.get_data(as_text=True))

            assert response_data['code'] == 'BAD_REQUEST'
            assert response_data['details']['missing_fields'] == missing_fields
            assert response_data['details']['invalid_fields'] == invalid_fields
            assert 'suggestion' in response_data['details']
            assert status_code == 400

    def test_error_handler_file_upload_error(self, app_context):
        """Test ErrorHandler.file_upload_error format"""
        with app_context.test_request_context():
            allowed_types = ['.xlsx', '.xls', '.csv']
            max_size_mb = 50

            response, status_code = ErrorHandler.file_upload_error(
                message="Invalid file type",
                allowed_types=allowed_types,
                max_size_mb=max_size_mb
            )

            response_data = json.loads(response.get_data(as_text=True))

            assert response_data['code'] == 'FILE_UPLOAD_ERROR'
            assert response_data['details']['allowed_file_types'] == allowed_types
            assert response_data['details']['max_file_size_mb'] == max_size_mb
            assert 'suggestion' in response_data['details']
            assert status_code == 400

    def test_error_handler_content_type_error(self, app_context):
        """Test ErrorHandler.content_type_error format"""
        with app_context.test_request_context('/test', headers={'Content-Type': 'text/plain'}):
            response, status_code = ErrorHandler.content_type_error()
            response_data = json.loads(response.get_data(as_text=True))

            assert response_data['code'] == 'INVALID_CONTENT_TYPE'
            assert response_data['details']['expected_content_type'] == 'application/json'
            assert response_data['details']['received_content_type'] == 'text/plain'
            assert 'suggestion' in response_data['details']
            assert status_code == 400

    def test_validation_utils_sanitize_string(self):
        """Test ValidationUtils.sanitize_string XSS protection"""
        # Test script tag removal
        malicious_input = "<script>alert('xss')</script>Hello World"
        sanitized = ValidationUtils.sanitize_string(malicious_input)
        assert "<script>" not in sanitized
        assert "Hello World" in sanitized

        # Test javascript protocol removal
        js_input = "javascript:alert('xss')"
        sanitized = ValidationUtils.sanitize_string(js_input)
        assert "javascript:" not in sanitized

        # Test event handler removal
        event_input = "onload=alert('xss')"
        sanitized = ValidationUtils.sanitize_string(event_input)
        assert "onload=" not in sanitized

        # Test iframe removal
        iframe_input = "<iframe src='evil.com'></iframe>Safe content"
        sanitized = ValidationUtils.sanitize_string(iframe_input)
        assert "<iframe" not in sanitized
        assert "Safe content" in sanitized

    def test_validation_utils_validate_file_upload(self):
        """Test ValidationUtils.validate_file_upload"""
        # Create a mock file object
        class MockFile:
            def __init__(self, filename='', content_length=None):
                self.filename = filename
                self.content_length = content_length

        # Test missing file
        with pytest.raises(ValidationError, match="No file selected"):
            ValidationUtils.validate_file_upload(MockFile())

        # Test invalid extension
        with pytest.raises(ValidationError, match="Invalid file type"):
            ValidationUtils.validate_file_upload(
                MockFile("test.txt"),
                allowed_extensions=['.xlsx', '.csv']
            )

        # Test file too large
        with pytest.raises(ValidationError, match="File too large"):
            ValidationUtils.validate_file_upload(
                MockFile("test.xlsx", content_length=100*1024*1024),  # 100MB
                allowed_extensions=['.xlsx'],
                max_size_mb=50
            )

        # Test path traversal
        with pytest.raises(ValidationError, match="path traversal detected"):
            ValidationUtils.validate_file_upload(
                MockFile("../../../etc/passwd"),
                allowed_extensions=['.txt']
            )

        # Test valid file
        assert ValidationUtils.validate_file_upload(
            MockFile("report.xlsx", content_length=1024*1024),  # 1MB
            allowed_extensions=['.xlsx', '.xls'],
            max_size_mb=50
        ) is True

    def test_validation_utils_validate_json_structure(self):
        """Test ValidationUtils.validate_json_structure"""
        # Test invalid data type
        with pytest.raises(ValidationError, match="Data must be a JSON object"):
            ValidationUtils.validate_json_structure("not a dict")

        # Test missing required fields
        with pytest.raises(ValidationError, match="Missing required fields"):
            ValidationUtils.validate_json_structure(
                {"field1": "value1"},
                required_fields=["field1", "field2"]
            )

        # Test extra fields
        with pytest.raises(ValidationError, match="Unexpected fields"):
            ValidationUtils.validate_json_structure(
                {"field1": "value1", "field2": "value2", "extra": "value"},
                required_fields=["field1"],
                optional_fields=["field2"]
            )

        # Test XSS sanitization
        data = {
            "name": "<script>alert('xss')</script>John",
            "description": "Safe content"
        }
        result = ValidationUtils.validate_json_structure(data)
        assert "<script>" not in result["name"]
        assert "John" in result["name"]
        assert result["description"] == "Safe content"

    def test_validation_utils_validate_id_format(self):
        """Test ValidationUtils.validate_id_format"""
        # Test empty ID
        with pytest.raises(ValidationError, match="id is required"):
            ValidationUtils.validate_id_format("")

        # Test invalid characters
        with pytest.raises(ValidationError, match="can only contain"):
            ValidationUtils.validate_id_format("invalid id with spaces")

        # Test valid ID
        valid_id = ValidationUtils.validate_id_format("valid_id-123")
        assert valid_id == "valid_id-123"

    def test_api_endpoint_error_responses(self, client, app_context):
        """Test actual API endpoints return standardized error responses"""
        # Test reports export endpoint with missing data
        response = client.post('/api/reports/export',
                              json={},
                              headers={'Content-Type': 'application/json'})

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        # Check standardized error format
        assert 'success' in data
        assert data['success'] is False
        assert 'message' in data
        assert 'timestamp' in data
        assert 'request_id' in data

    def test_api_endpoint_invalid_content_type(self, client):
        """Test API endpoints handle invalid content type correctly"""
        response = client.post('/api/reports/export',
                              data="not json",
                              headers={'Content-Type': 'text/plain'})

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        # Should use standardized content type error format
        assert data.get('code') == 'INVALID_CONTENT_TYPE'
        assert 'expected_content_type' in data.get('details', {})

    def test_api_endpoint_file_upload_validation(self, client):
        """Test file upload endpoints validate files correctly"""
        # Test enhanced report upload without file
        response = client.post('/api/enhanced-report/upload-excel')

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        # Should use standardized file upload error format
        assert data.get('code') == 'FILE_UPLOAD_ERROR'
        assert 'allowed_file_types' in data.get('details', {})

    def test_request_id_tracking(self, client, app_context):
        """Test that request IDs are properly tracked"""
        response = client.post('/api/reports/export', json={})

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        # Check request ID is present and valid UUID format
        request_id = data.get('request_id')
        assert request_id is not None
        assert len(request_id) == 36  # UUID format
        assert request_id.count('-') == 4  # UUID has 4 dashes

    def test_debug_info_in_development(self, app_context):
        """Test that debug info is included in development mode"""
        app_context.config['DEBUG'] = True

        with app_context.test_request_context('/test'):
            response, status_code = ErrorHandler.format_error_response(
                message="Test error"
            )

            response_data = json.loads(response.get_data(as_text=True))
            assert 'debug_info' in response_data
            assert 'endpoint' in response_data['debug_info']
            assert 'method' in response_data['debug_info']


def run_tests():
    """Run the test suite"""
    print("🧪 Running HTTP 400 Error Handling Tests...")

    # Run with pytest
    pytest_args = [
        __file__,
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--color=yes'  # Colored output
    ]

    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    return exit_code


if __name__ == '__main__':
    run_tests()