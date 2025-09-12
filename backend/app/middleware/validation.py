"""
Validation Middleware using Pydantic

This module provides comprehensive request/response validation using Pydantic models.
It includes input sanitization, XSS protection, SQL injection prevention, and
detailed validation error handling.
"""

import json
import logging
import re
import hashlib
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union, get_type_hints
from functools import wraps
from datetime import datetime

from flask import Flask, Request, Response, request, jsonify, current_app, g
from pydantic import BaseModel, ValidationError, create_model
from pydantic.error_wrappers import ErrorList
from werkzeug.exceptions import BadRequest, UnprocessableEntity

from ..core.exceptions import ValidationError as CustomValidationError
from ..schemas.common import ValidationErrorResponse

logger = logging.getLogger(__name__)

class ValidationMiddleware:
    """Middleware for validating requests and responses using Pydantic models."""
    
    def __init__(self, app: Flask):
        """Initialize validation middleware."""
        self.app = app
        self.validation_cache = {}
        self.rate_limit_cache = {}
        
        # Register with Flask app
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        
        # Validation configuration
        self.config = {
            'enable_request_validation': True,
            'enable_response_validation': True,
            'enable_input_sanitization': True,
            'enable_sql_injection_protection': True,
            'enable_xss_protection': True,
            'strict_validation': True,
            'log_validation_errors': True,
            'return_detailed_errors': True,
            'max_validation_errors': 10,
            'validation_timeout': 5.0,  # seconds
        }
        
        # Load configuration from app config
        self._load_config()
    
    def _load_config(self):
        """Load validation configuration from Flask app config."""
        for key in self.config:
            config_key = f'VALIDATION_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[config_key]
    
    def _before_request(self):
        """Process request before it reaches the route handler."""
        if not self.config['enable_request_validation']:
            return
        
        # Store request start time for validation timing
        g.request_start_time = time.time()
        
        # Basic request validation
        self._validate_basic_request()
        
        # Input sanitization
        if self.config['enable_input_sanitization']:
            self._sanitize_request_inputs()
        
        # SQL injection protection
        if self.config['enable_sql_injection_protection']:
            self._check_sql_injection()
        
        # XSS protection
        if self.config['enable_xss_protection']:
            self._check_xss_attempts()
    
    def _after_request(self, response: Response):
        """Process response after route handler completes."""
        if not self.config['enable_response_validation']:
            return response
        
        # Response validation timing
        if hasattr(g, 'request_start_time'):
            validation_time = time.time() - g.request_start_time
            if validation_time > self.config['validation_timeout']:
                logger.warning(f'Request validation took {validation_time:.2f}s, exceeding timeout')
        
        # Add validation headers
        response.headers['X-Validation-Status'] = 'validated'
        response.headers['X-Validation-Time'] = str(validation_time)
        
        return response
    
    def _validate_basic_request(self):
        """Perform basic request validation."""
        # Check request size limits
        max_content_length = self.app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16MB
        if request.content_length and request.content_length > max_content_length:
            raise BadRequest('Request too large')
        
        # Check content type for JSON requests
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            if not request.get_json(silent=True):
                raise BadRequest('Invalid JSON payload')
    
    def _sanitize_request_inputs(self):
        """Sanitize request inputs to prevent XSS and injection attacks."""
        # Sanitize query parameters
        for key, value in request.args.items():
            if isinstance(value, str):
                request.args[key] = self._sanitize_string(value)
        
        # Sanitize form data
        for key, value in request.form.items():
            if isinstance(value, str):
                request.form[key] = self._sanitize_string(value)
        
        # Sanitize JSON data
        if request.is_json:
            json_data = request.get_json()
            if json_data:
                sanitized_data = self._sanitize_dict(json_data)
                # Replace request data with sanitized version
                request._cached_json = sanitized_data
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string value."""
        if not isinstance(value, str):
            return value
        
        # Remove dangerous HTML/JavaScript
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'vbscript:',   # VBScript protocol
            r'data:',       # Data URLs
            r'on\w+\s*=',   # Event handlers
            r'<iframe[^>]*>',  # Iframe tags
            r'<object[^>]*>',  # Object tags
            r'<embed[^>]*>',   # Embed tags
        ]
        
        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # HTML entity encoding for safety
        html_entities = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, entity in html_entities.items():
            sanitized = sanitized.replace(char, entity)
        
        return sanitized
    
    def _sanitize_dict(self, data: Any) -> Any:
        """Recursively sanitize dictionary values."""
        if isinstance(data, dict):
            return {key: self._sanitize_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _check_sql_injection(self):
        """Check for potential SQL injection attempts."""
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
            r'(\b(and|or)\s+\d+\s*=\s*\d+)',
            r'(\b(and|or)\s+\w+\s*=\s*\w+)',
            r'(\b(and|or)\s+\w+\s*like\s*[\'"]%)',
            r'(\b(and|or)\s+\w+\s*in\s*\([^)]*\))',
            r'(\b(and|or)\s+\w+\s*between\s+\w+\s+and\s+\w+)',
            r'(\b(and|or)\s+\w+\s*is\s+null)',
            r'(\b(and|or)\s+\w+\s*is\s+not\s+null)',
            r'(\b(and|or)\s+\w+\s*exists\s*\([^)]*\))',
            r'(\b(and|or)\s+\w+\s*not\s+exists\s*\([^)]*\))',
        ]
        
        # Check query parameters
        for key, value in request.args.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f'Potential SQL injection detected in query param {key}: {value}')
                        raise BadRequest('Invalid input detected')
        
        # Check form data
        for key, value in request.form.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f'Potential SQL injection detected in form field {key}: {value}')
                        raise BadRequest('Invalid input detected')
        
        # Check JSON data
        if request.is_json:
            json_data = request.get_json()
            if json_data:
                self._check_dict_sql_injection(json_data)
    
    def _check_dict_sql_injection(self, data: Any, path: str = ""):
        """Recursively check dictionary for SQL injection patterns."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                self._check_dict_sql_injection(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                self._check_dict_sql_injection(item, current_path)
        elif isinstance(data, str):
            sql_patterns = [
                r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
                r'(\b(and|or)\s+\d+\s*=\s*\d+)',
                r'(\b(and|or)\s+\w+\s*=\s*\w+)',
                r'(\b(and|or)\s+\w+\s*like\s*[\'"]%)',
                r'(\b(and|or)\s+\w+\s*in\s*\([^)]*\))',
                r'(\b(and|or)\s+\w+\s*between\s+\w+\s+and\s+\w+)',
                r'(\b(and|or)\s+\w+\s*is\s+null)',
                r'(\b(and|or)\s+\w+\s*is\s+not\s+null)',
                r'(\b(and|or)\s+\w+\s*exists\s*\([^)]*\))',
                r'(\b(and|or)\s+\w+\s*not\s+exists\s*\([^)]*\))',
            ]
            
            for pattern in sql_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    logger.warning(f'Potential SQL injection detected in {path}: {data}')
                    raise BadRequest('Invalid input detected')
    
    def _check_xss_attempts(self):
        """Check for potential XSS attempts."""
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'data:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<form[^>]*>',
            r'<input[^>]*>',
            r'<textarea[^>]*>',
            r'<button[^>]*>',
            r'<select[^>]*>',
            r'<option[^>]*>',
            r'<label[^>]*>',
            r'<fieldset[^>]*>',
            r'<legend[^>]*>',
            r'<optgroup[^>]*>',
            r'<datalist[^>]*>',
            r'<output[^>]*>',
        ]
        
        # Check query parameters
        for key, value in request.args.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f'Potential XSS detected in query param {key}: {value}')
                        raise BadRequest('Invalid input detected')
        
        # Check form data
        for key, value in request.form.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f'Potential XSS detected in form field {key}: {value}')
                        raise BadRequest('Invalid input detected')
        
        # Check JSON data
        if request.is_json:
            json_data = request.get_json()
            if json_data:
                self._check_dict_xss(json_data)
    
    def _check_dict_xss(self, data: Any, path: str = ""):
        """Recursively check dictionary for XSS patterns."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                self._check_dict_xss(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                self._check_dict_xss(item, current_path)
        elif isinstance(data, str):
            xss_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'data:',
                r'on\w+\s*=',
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>',
                r'<form[^>]*>',
                r'<input[^>]*>',
                r'<textarea[^>]*>',
                r'<button[^>]*>',
                r'<select[^>]*>',
                r'<option[^>]*>',
                r'<label[^>]*>',
                r'<fieldset[^>]*>',
                r'<legend[^>]*>',
                r'<optgroup[^>]*>',
                r'<datalist[^>]*>',
                r'<output[^>]*>',
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    logger.warning(f'Potential XSS detected in {path}: {data}')
                    raise BadRequest('Invalid input detected')

def validate_request(schema: Type[BaseModel], 
                    strict: bool = True, 
                    sanitize: bool = True,
                    log_errors: bool = True) -> Callable:
    """
    Decorator to validate request data using Pydantic schema.
    
    Args:
        schema: Pydantic model class for validation
        strict: Whether to use strict validation mode
        sanitize: Whether to sanitize input data
        log_errors: Whether to log validation errors
    
    Returns:
        Decorated function with validation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get request data based on method
                if request.method == 'GET':
                    data = dict(request.args)
                elif request.is_json:
                    data = request.get_json() or {}
                elif request.form:
                    data = dict(request.form)
                elif request.files:
                    data = {'files': request.files}
                else:
                    data = {}
                
                # Sanitize data if requested
                if sanitize:
                    data = _sanitize_data(data)
                
                # Validate data against schema
                validated_data = schema(**data)
                
                # Store validated data in request context
                request.validated_data = validated_data
                
                # Call original function
                return func(*args, **kwargs)
                
            except ValidationError as e:
                if log_errors:
                    logger.error(f'Request validation failed: {e}')
                
                # Create detailed error response
                error_response = _create_validation_error_response(e)
                
                return jsonify(error_response), 422
                
            except Exception as e:
                if log_errors:
                    logger.error(f'Unexpected error during validation: {e}')
                raise
        
        return wrapper
    return decorator

def validate_response(schema: Type[BaseModel], 
                     strict: bool = True,
                     log_errors: bool = True) -> Callable:
    """
    Decorator to validate response data using Pydantic schema.
    
    Args:
        schema: Pydantic model class for validation
        strict: Whether to use strict validation mode
        log_errors: Whether to log validation errors
    
    Returns:
        Decorated function with response validation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Call original function
            response = func(*args, **kwargs)
            
            try:
                # Extract response data
                if isinstance(response, tuple):
                    response_data, status_code = response
                else:
                    response_data = response
                    status_code = 200
                
                # Skip validation for error responses
                if status_code >= 400:
                    return response
                
                # Validate response data
                if isinstance(response_data, dict):
                    validated_response = schema(**response_data)
                    # Replace with validated data
                    if isinstance(response, tuple):
                        return validated_response.dict(), status_code
                    else:
                        return validated_response.dict()
                
                return response
                
            except ValidationError as e:
                if log_errors:
                    logger.error(f'Response validation failed: {e}')
                
                # Return validation error response
                error_response = _create_validation_error_response(e)
                return jsonify(error_response), 422
                
            except Exception as e:
                if log_errors:
                    logger.error(f'Unexpected error during response validation: {e}')
                return response
        
        return wrapper
    return decorator

def _sanitize_data(data: Any) -> Any:
    """Sanitize data recursively."""
    if isinstance(data, dict):
        return {key: _sanitize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_sanitize_data(item) for item in data]
    elif isinstance(data, str):
        return _sanitize_string(data)
    else:
        return data

def _sanitize_string(value: str) -> str:
    """Sanitize a string value."""
    if not isinstance(value, str):
        return value
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    sanitized = value
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # HTML entity encoding
    html_entities = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#x27;'
    }
    
    for char, entity in html_entities.items():
        sanitized = sanitized.replace(char, entity)
    
    return sanitized

def _create_validation_error_response(validation_error: ValidationError) -> Dict[str, Any]:
    """Create a standardized validation error response."""
    field_errors = {}
    
    for error in validation_error.errors():
        field_name = '.'.join(str(loc) for loc in error['loc'])
        error_message = error['msg']
        
        if field_name not in field_errors:
            field_errors[field_name] = []
        
        field_errors[field_name].append(error_message)
    
    return ValidationErrorResponse(
        success=False,
        error="VALIDATION_ERROR",
        message="Request validation failed",
        field_errors=field_errors,
        timestamp=datetime.utcnow()
    ).dict()

# Utility functions for common validation patterns
def validate_file_upload(allowed_types: List[str] = None,
                        max_size: int = None,
                        required: bool = True) -> Callable:
    """Decorator to validate file uploads."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if required and not request.files:
                raise BadRequest('File upload is required')
            
            if request.files:
                for file_key, file_obj in request.files.items():
                    if file_obj.filename:
                        # Check file type
                        if allowed_types:
                            file_ext = file_obj.filename.rsplit('.', 1)[1].lower() if '.' in file_obj.filename else ''
                            if file_ext not in allowed_types:
                                raise BadRequest(f'File type {file_ext} not allowed')
                        
                        # Check file size
                        if max_size:
                            file_obj.seek(0, 2)  # Seek to end
                            file_size = file_obj.tell()
                            file_obj.seek(0)  # Reset to beginning
                            
                            if file_size > max_size:
                                raise BadRequest(f'File size exceeds maximum allowed size')
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_pagination(default_page: int = 1,
                       default_per_page: int = 20,
                       max_per_page: int = 100) -> Callable:
    """Decorator to validate pagination parameters."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                page = int(request.args.get('page', default_page))
                per_page = int(request.args.get('per_page', default_per_page))
                
                if page < 1:
                    page = default_page
                if per_page < 1 or per_page > max_per_page:
                    per_page = default_per_page
                
                # Store validated pagination in request context
                request.pagination = {
                    'page': page,
                    'per_page': per_page,
                    'offset': (page - 1) * per_page
                }
                
                return func(*args, **kwargs)
                
            except ValueError:
                raise BadRequest('Invalid pagination parameters')
        return wrapper
    return decorator

def validate_search_query(min_length: int = 1,
                         max_length: int = 100,
                         allowed_chars: str = None) -> Callable:
    """Decorator to validate search query parameters."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            query = request.args.get('query', '').strip()
            
            if query:
                if len(query) < min_length:
                    raise BadRequest(f'Search query must be at least {min_length} characters')
                
                if len(query) > max_length:
                    raise BadRequest(f'Search query cannot exceed {max_length} characters')
                
                if allowed_chars:
                    invalid_chars = [char for char in query if char not in allowed_chars]
                    if invalid_chars:
                        raise BadRequest(f'Search query contains invalid characters: {invalid_chars}')
                
                # Store validated query in request context
                request.search_query = query
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
