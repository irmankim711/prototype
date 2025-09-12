"""
Logging Middleware

This module provides comprehensive request/response logging with sanitization capabilities.
It includes structured logging, performance monitoring, and security event logging.
"""

import json
import logging
import time
import hashlib
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from flask import Flask, Request, Response, request, jsonify, current_app, g
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """Middleware for comprehensive request logging."""
    
    def __init__(self, app: Flask):
        """Initialize request logging middleware."""
        self.app = app
        
        # Logging configuration
        self.config = {
            'enable_request_logging': True,
            'enable_response_logging': True,
            'enable_performance_logging': True,
            'enable_security_logging': True,
            'log_request_body': True,
            'log_response_body': False,  # Usually disabled for security
            'log_headers': True,
            'log_cookies': False,  # Usually disabled for security
            'log_query_params': True,
            'log_user_agent': True,
            'log_ip_address': True,
            'log_user_id': True,
            'sanitize_sensitive_data': True,
            'sensitive_fields': ['password', 'token', 'secret', 'key', 'authorization'],
            'max_body_size': 1024,  # Max body size to log
            'log_format': 'json',  # json, text, structured
            'log_level': 'INFO',
            'log_to_file': False,
            'log_file_path': 'logs/requests.log',
            'log_rotation': 'daily',
            'log_compression': True,
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Register with Flask app
        self._register_logging()
    
    def _load_config(self):
        """Load logging configuration from Flask app config."""
        for key in self.config:
            config_key = f'LOGGING_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[config_key]
    
    def _setup_logging(self):
        """Setup logging configuration."""
        if self.config['log_to_file']:
            self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Setup file logging with rotation."""
        import os
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.config['log_file_path'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup rotating file handler
        handler = RotatingFileHandler(
            self.config['log_file_path'],
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        # Set formatter
        if self.config['log_format'] == 'json':
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, self.config['log_level']))
    
    def _register_logging(self):
        """Register logging middleware with Flask app."""
        @self.app.before_request
        def before_request():
            if not self.config['enable_request_logging']:
                return
            
            # Store request start time
            g.request_start_time = time.time()
            
            # Log request
            self._log_request()
        
        @self.app.after_request
        def after_request(response: Response):
            if not self.config['enable_response_logging']:
                return response
            
            # Log response
            self._log_response(response)
            
            return response
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            # Log exceptions
            self._log_exception(e)
            raise e
    
    def _log_request(self):
        """Log incoming request details."""
        try:
            # Basic request info
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'request',
                'method': request.method,
                'url': request.url,
                'endpoint': request.endpoint,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'content_type': request.content_type,
                'content_length': request.content_length,
            }
            
            # Add user ID if available
            if self.config['log_user_id']:
                user_id = self._get_current_user_id()
                if user_id:
                    log_data['user_id'] = user_id
            
            # Add query parameters
            if self.config['log_query_params'] and request.args:
                log_data['query_params'] = self._sanitize_data(dict(request.args))
            
            # Add headers
            if self.config['log_headers']:
                headers = dict(request.headers)
                if not self.config['log_cookies']:
                    headers.pop('Cookie', None)
                log_data['headers'] = self._sanitize_data(headers)
            
            # Add cookies
            if self.config['log_cookies']:
                log_data['cookies'] = self._sanitize_data(dict(request.cookies))
            
            # Add request body
            if self.config['log_request_body'] and request.is_json:
                body = request.get_json(silent=True)
                if body:
                    log_data['body'] = self._sanitize_data(body)
            
            # Log the request
            self._log_data(log_data, 'INFO')
            
        except Exception as e:
            logger.error(f'Error logging request: {e}')
    
    def _log_response(self, response: Response):
        """Log response details."""
        try:
            # Calculate response time
            response_time = 0
            if hasattr(g, 'request_start_time'):
                response_time = (time.time() - g.request_start_time) * 1000  # Convert to milliseconds
            
            # Basic response info
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'response',
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'content_type': response.content_type,
                'content_length': response.content_length,
            }
            
            # Add response headers
            if self.config['log_headers']:
                log_data['headers'] = dict(response.headers)
            
            # Add response body (if enabled and safe)
            if self.config['log_response_body'] and response.status_code < 400:
                try:
                    if response.is_json:
                        body = response.get_json()
                        if body:
                            log_data['body'] = self._sanitize_data(body)
                except:
                    pass  # Skip if response body can't be parsed
            
            # Log the response
            self._log_data(log_data, 'INFO')
            
        except Exception as e:
            logger.error(f'Error logging response: {e}')
    
    def _log_exception(self, exception: Exception):
        """Log exception details."""
        try:
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'exception',
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'endpoint': request.endpoint if request else None,
                'method': request.method if request else None,
                'url': request.url if request else None,
                'remote_addr': request.remote_addr if request else None,
            }
            
            # Add user ID if available
            if self.config['log_user_id']:
                user_id = self._get_current_user_id()
                if user_id:
                    log_data['user_id'] = user_id
            
            # Add stack trace for non-HTTP exceptions
            if not isinstance(exception, HTTPException):
                import traceback
                log_data['stack_trace'] = traceback.format_exc()
            
            # Log the exception
            self._log_data(log_data, 'ERROR')
            
        except Exception as e:
            logger.error(f'Error logging exception: {e}')
    
    def _log_data(self, data: Dict[str, Any], level: str):
        """Log data with specified level."""
        try:
            if self.config['log_format'] == 'json':
                message = json.dumps(data, default=str)
            else:
                # Convert to text format
                message = self._format_text_log(data)
            
            if level == 'INFO':
                logger.info(message)
            elif level == 'WARNING':
                logger.warning(message)
            elif level == 'ERROR':
                logger.error(message)
            elif level == 'DEBUG':
                logger.debug(message)
            else:
                logger.info(message)
                
        except Exception as e:
            logger.error(f'Error formatting log message: {e}')
    
    def _format_text_log(self, data: Dict[str, Any]) -> str:
        """Format log data as text."""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}: {json.dumps(value, default=str)}")
            else:
                lines.append(f"{key}: {value}")
        return " | ".join(lines)
    
    def _get_current_user_id(self) -> Optional[str]:
        """Get current user ID from JWT token."""
        try:
            from flask_jwt_extended import get_jwt_identity
            return get_jwt_identity()
        except:
            return None
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize sensitive data."""
        if not self.config['sanitize_sensitive_data']:
            return data
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if self._is_sensitive_field(key):
                    sanitized[key] = '***REDACTED***'
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        else:
            return data
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if field name contains sensitive information."""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.config['sensitive_fields'])

class ResponseLoggingMiddleware:
    """Middleware for response-specific logging."""
    
    def __init__(self, app: Flask):
        """Initialize response logging middleware."""
        self.app = app
        
        # Response logging configuration
        self.config = {
            'enable_response_logging': True,
            'log_success_responses': True,
            'log_error_responses': True,
            'log_slow_responses': True,
            'slow_response_threshold': 1000,  # milliseconds
            'log_response_size': True,
            'log_response_headers': False,
            'log_response_body_for_errors': True,
            'max_error_body_size': 2048,
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Register with Flask app
        self._register_response_logging()
    
    def _load_config(self):
        """Load response logging configuration from Flask app config."""
        for key in self.config:
            config_key = f'RESPONSE_LOGGING_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[key]
    
    def _register_response_logging(self):
        """Register response logging with Flask app."""
        @self.app.after_request
        def after_request(response: Response):
            if not self.config['enable_response_logging']:
                return response
            
            # Log response based on configuration
            self._log_response_details(response)
            
            return response
    
    def _log_response_details(self, response: Response):
        """Log detailed response information."""
        try:
            # Calculate response time
            response_time = 0
            if hasattr(g, 'request_start_time'):
                response_time = (time.time() - g.request_start_time) * 1000
            
            # Log slow responses
            if self.config['log_slow_responses'] and response_time > self.config['slow_response_threshold']:
                self._log_slow_response(response, response_time)
            
            # Log error responses
            if self.config['log_error_responses'] and response.status_code >= 400:
                self._log_error_response(response, response_time)
            
            # Log success responses
            elif self.config['log_success_responses'] and response.status_code < 400:
                self._log_success_response(response, response_time)
            
        except Exception as e:
            logger.error(f'Error logging response details: {e}')
    
    def _log_slow_response(self, response: Response, response_time: float):
        """Log slow response details."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'slow_response',
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url,
            'status_code': response.status_code,
            'response_time_ms': round(response_time, 2),
            'threshold_ms': self.config['slow_response_threshold'],
        }
        
        self._log_data(log_data, 'WARNING')
    
    def _log_error_response(self, response: Response, response_time: float):
        """Log error response details."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'error_response',
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url,
            'status_code': response.status_code,
            'response_time_ms': round(response_time, 2),
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
        }
        
        # Add user ID if available
        user_id = self._get_current_user_id()
        if user_id:
            log_data['user_id'] = user_id
        
        # Add response body for errors if enabled
        if self.config['log_response_body_for_errors']:
            try:
                if response.is_json:
                    body = response.get_json()
                    if body:
                        # Truncate body if too long
                        body_str = json.dumps(body)
                        if len(body_str) > self.config['max_error_body_size']:
                            body_str = body_str[:self.config['max_error_body_size']] + '...'
                        log_data['response_body'] = body_str
            except:
                pass
        
        self._log_data(log_data, 'ERROR')
    
    def _log_success_response(self, response: Response, response_time: float):
        """Log success response details."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'success_response',
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url,
            'status_code': response.status_code,
            'response_time_ms': round(response_time, 2),
        }
        
        # Add response size if enabled
        if self.config['log_response_size']:
            log_data['response_size'] = response.content_length or 0
        
        self._log_data(log_data, 'INFO')
    
    def _log_data(self, data: Dict[str, Any], level: str):
        """Log data with specified level."""
        try:
            message = json.dumps(data, default=str)
            
            if level == 'INFO':
                logger.info(message)
            elif level == 'WARNING':
                logger.warning(message)
            elif level == 'ERROR':
                logger.error(message)
            else:
                logger.info(message)
                
        except Exception as e:
            logger.error(f'Error formatting log message: {e}')
    
    def _get_current_user_id(self) -> Optional[str]:
        """Get current user ID from JWT token."""
        try:
            from flask_jwt_extended import get_jwt_identity
            return get_jwt_identity()
        except:
            return None

# Utility functions for logging
def log_request_info(f: Callable) -> Callable:
    """Decorator to log request information."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request info
        logger.info(f'Request to {f.__name__} from {request.remote_addr}')
        return f(*args, **kwargs)
    return decorated_function

def log_response_time(f: Callable) -> Callable:
    """Decorator to log response time."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        response_time = (time.time() - start_time) * 1000
        logger.info(f'{f.__name__} took {response_time:.2f}ms')
        return result
    return decorated_function

def log_security_event(event_type: str, details: Dict[str, Any] = None):
    """Log security-related events."""
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'type': 'security_event',
        'event_type': event_type,
        'details': details or {},
        'remote_addr': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent', 'Unknown') if request else None,
    }
    
    # Add user ID if available
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        if user_id:
            log_data['user_id'] = user_id
    except:
        pass
    
    logger.warning(json.dumps(log_data, default=str))

def log_performance_metric(metric_name: str, value: float, unit: str = 'ms'):
    """Log performance metrics."""
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'type': 'performance_metric',
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'endpoint': request.endpoint if request else None,
    }
    
    logger.info(json.dumps(log_data, default=str))
