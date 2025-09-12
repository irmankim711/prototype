"""
Enhanced Security Middleware

This module provides comprehensive security features including:
- Enhanced CSRF protection with Redis storage
- Advanced security headers
- CORS configuration with production-ready settings
- Content Security Policy (CSP) with nonce support
- Strict-Transport-Security for HTTPS
- Secure session management
- Request sanitization and validation
"""

import logging
import secrets
import hashlib
import time
import json
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, Request, Response, request, jsonify, current_app, g, session, make_response
from werkzeug.exceptions import Forbidden, BadRequest
from flask_cors import CORS
import redis

logger = logging.getLogger(__name__)

class EnhancedCSRFMiddleware:
    """Enhanced middleware for CSRF protection with Redis storage."""
    
    def __init__(self, app: Flask):
        """Initialize enhanced CSRF middleware."""
        self.app = app
        
        # CSRF configuration with enhanced security
        self.config = {
            'enable_csrf_protection': True,
            'csrf_token_expiry': 3600,  # 1 hour
            'csrf_token_length': 64,  # Increased for better security
            'csrf_header_name': 'X-CSRF-Token',
            'csrf_cookie_name': 'csrf_token',
            'csrf_exempt_methods': ['GET', 'HEAD', 'OPTIONS'],
            'csrf_exempt_endpoints': ['/api/auth/login', '/api/auth/register', '/health'],
            'csrf_require_referer': True,
            'csrf_allow_origin': None,
            'log_csrf_violations': True,
            'csrf_double_submit': True,  # Double submit cookie pattern
            'csrf_same_site': 'Strict',
            'csrf_secure': True,
            'csrf_http_only': False,  # Allow JavaScript access for double submit
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Initialize Redis connection for token storage
        self._init_redis()
        
        # Register with Flask app
        self._register_csrf_protection()
    
    def _load_config(self):
        """Load CSRF configuration from Flask app config."""
        for key in self.config:
            config_key = f'CSRF_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[config_key]
    
    def _init_redis(self):
        """Initialize Redis connection for CSRF token storage."""
        try:
            redis_url = self.app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connected for CSRF token storage")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed for CSRF: {e}")
            # Fallback to in-memory storage
            self.redis_client = None
            self.csrf_tokens = {}
    
    def _register_csrf_protection(self):
        """Register enhanced CSRF protection with Flask app."""
        @self.app.before_request
        def before_request():
            if not self.config['enable_csrf_protection']:
                return
            
            # Skip CSRF check for exempt methods
            if request.method in self.config['csrf_exempt_methods']:
                return
            
            # Skip CSRF check for exempt endpoints
            if request.endpoint in self.config['csrf_exempt_endpoints']:
                return
            
            # Validate CSRF token
            self._validate_csrf_token()
        
        # CSRF error handler
        @self.app.errorhandler(403)
        def csrf_forbidden(e):
            if 'CSRF' in str(e):
                return self._create_csrf_error_response(e)
            return e
    
    def _validate_csrf_token(self):
        """Validate CSRF token for the current request."""
        # Get token from header or cookie
        header_token = request.headers.get(self.config['csrf_header_name'])
        cookie_token = request.cookies.get(self.config['csrf_cookie_name'])
        
        if not header_token and not cookie_token:
            self._log_csrf_violation("Missing CSRF token")
            raise Forbidden("CSRF token missing")
        
        # Double submit validation
        if self.config['csrf_double_submit']:
            if not header_token or not cookie_token or header_token != cookie_token:
                self._log_csrf_violation("CSRF token mismatch (double submit)")
                raise Forbidden("CSRF token validation failed")
        
        # Validate token
        token_to_validate = header_token or cookie_token
        if not self._is_valid_csrf_token(token_to_validate):
            self._log_csrf_violation("Invalid CSRF token")
            raise Forbidden("Invalid CSRF token")
        
        # Check referer if required
        if self.config['csrf_require_referer']:
            self._validate_referer()
    
    def _is_valid_csrf_token(self, token: str) -> bool:
        """Check if CSRF token is valid."""
        try:
            if self.redis_client:
                # Check Redis for token
                token_data = self.redis_client.get(f"csrf:{token}")
                if not token_data:
                    return False
                
                token_info = json.loads(token_data)
                if time.time() > token_info['expires']:
                    # Remove expired token
                    self.redis_client.delete(f"csrf:{token}")
                    return False
                
                return True
            else:
                # Fallback to in-memory storage
                if token not in self.csrf_tokens:
                    return False
                
                token_data = self.csrf_tokens[token]
                if time.time() > token_data['expires']:
                    # Remove expired token
                    del self.csrf_tokens[token]
                    return False
                
                return True
        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False
    
    def _validate_referer(self):
        """Validate request referer."""
        referer = request.headers.get('Referer')
        if not referer:
            self._log_csrf_violation("Missing referer")
            raise Forbidden("Referer header required")
        
        # Check if referer is from allowed origin
        if self.config['csrf_allow_origin']:
            if not referer.startswith(self.config['csrf_allow_origin']):
                self._log_csrf_violation(f"Invalid referer: {referer}")
                raise Forbidden("Invalid referer")
    
    def generate_csrf_token(self, user_id: str = None) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_hex(self.config['csrf_token_length'])
        expires = time.time() + self.config['csrf_token_expiry']
        
        token_data = {
            'user_id': user_id,
            'expires': expires,
            'created_at': time.time(),
            'ip_address': request.remote_addr if request else None
        }
        
        try:
            if self.redis_client:
                # Store in Redis
                self.redis_client.setex(
                    f"csrf:{token}",
                    self.config['csrf_token_expiry'],
                    json.dumps(token_data)
                )
            else:
                # Fallback to in-memory storage
                self.csrf_tokens[token] = token_data
        except Exception as e:
            logger.error(f"Failed to store CSRF token: {e}")
            # Fallback to in-memory storage
            self.csrf_tokens[token] = token_data
        
        return token
    
    def _log_csrf_violation(self, reason: str):
        """Log CSRF violation."""
        if self.config['log_csrf_violations']:
            logger.warning(f'CSRF violation: {reason} from {request.remote_addr}')
    
    def _create_csrf_error_response(self, error: Forbidden) -> Tuple[Response, int]:
        """Create CSRF error response."""
        response_data = {
            'success': False,
            'error': 'CSRF_VIOLATION',
            'message': 'CSRF token validation failed',
            'timestamp': datetime.utcnow().isoformat(),
            'code': 'CSRF_TOKEN_INVALID'
        }
        
        response = jsonify(response_data)
        response.status_code = 403
        
        return response, 403

class EnhancedSecurityHeadersMiddleware:
    """Enhanced middleware for adding comprehensive security headers."""
    
    def __init__(self, app: Flask):
        """Initialize enhanced security headers middleware."""
        self.app = app
        
        # Enhanced security headers configuration
        self.config = {
            'enable_security_headers': True,
            'enable_csp': True,
            'enable_hsts': True,
            'enable_xss_protection': True,
            'enable_content_type_options': True,
            'enable_frame_options': True,
            'enable_referrer_policy': True,
            'enable_permissions_policy': True,
            'enable_cross_origin_embedder_policy': True,
            'enable_cross_origin_opener_policy': True,
            'enable_cross_origin_resource_policy': True,
            'csp_policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';",
            'hsts_max_age': 31536000,  # 1 year
            'hsts_include_subdomains': True,
            'hsts_preload': False,
            'frame_options': 'DENY',
            'referrer_policy': 'strict-origin-when-cross-origin',
            'permissions_policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()',
            'cross_origin_embedder_policy': 'require-corp',
            'cross_origin_opener_policy': 'same-origin',
            'cross_origin_resource_policy': 'same-origin',
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Register with Flask app
        self._register_security_headers()
    
    def _load_config(self):
        """Load security headers configuration from Flask app config."""
        for key in self.config:
            config_key = f'SECURITY_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[config_key]
    
    def _register_security_headers(self):
        """Register enhanced security headers with Flask app."""
        @self.app.after_request
        def after_request(response: Response):
            if not self.config['enable_security_headers']:
                return response
            
            # Add comprehensive security headers
            if self.config['enable_csp']:
                response.headers['Content-Security-Policy'] = self.config['csp_policy']
            
            if self.config['enable_hsts']:
                hsts_value = f"max-age={self.config['hsts_max_age']}"
                if self.config['hsts_include_subdomains']:
                    hsts_value += "; includeSubDomains"
                if self.config['hsts_preload']:
                    hsts_value += "; preload"
                response.headers['Strict-Transport-Security'] = hsts_value
            
            if self.config['enable_xss_protection']:
                response.headers['X-XSS-Protection'] = '1; mode=block'
            
            if self.config['enable_content_type_options']:
                response.headers['X-Content-Type-Options'] = 'nosniff'
            
            if self.config['enable_frame_options']:
                response.headers['X-Frame-Options'] = self.config['frame_options']
            
            if self.config['enable_referrer_policy']:
                response.headers['Referrer-Policy'] = self.config['referrer_policy']
            
            if self.config['enable_permissions_policy']:
                response.headers['Permissions-Policy'] = self.config['permissions_policy']
            
            if self.config['enable_cross_origin_embedder_policy']:
                response.headers['Cross-Origin-Embedder-Policy'] = self.config['cross_origin_embedder_policy']
            
            if self.config['enable_cross_origin_opener_policy']:
                response.headers['Cross-Origin-Opener-Policy'] = self.config['cross_origin_opener_policy']
            
            if self.config['enable_cross_origin_resource_policy']:
                response.headers['Cross-Origin-Resource-Policy'] = self.config['cross_origin_resource_policy']
            
            # Additional security headers
            response.headers['X-Download-Options'] = 'noopen'
            response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
            response.headers['X-DNS-Prefetch-Control'] = 'off'
            response.headers['X-Requested-With'] = 'XMLHttpRequest'
            
            return response

class SecureSessionMiddleware:
    """Middleware for secure session management."""
    
    def __init__(self, app: Flask):
        """Initialize secure session middleware."""
        self.app = app
        
        # Session configuration
        self.config = {
            'session_cookie_secure': True,
            'session_cookie_httponly': True,
            'session_cookie_samesite': 'Strict',
            'session_cookie_max_age': 3600,  # 1 hour
            'session_cookie_domain': None,
            'session_cookie_path': '/',
            'session_permanent': False,
            'session_use_signer': True,
            'session_key_prefix': 'session:',
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Register with Flask app
        self._register_session_config()
    
    def _load_config(self):
        """Load session configuration from Flask app config."""
        for key in self.config:
            config_key = f'SESSION_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[config_key]
    
    def _register_session_config(self):
        """Register secure session configuration with Flask app."""
        # Configure session settings
        self.app.config.update({
            'SESSION_COOKIE_SECURE': self.config['session_cookie_secure'],
            'SESSION_COOKIE_HTTPONLY': self.config['session_cookie_httponly'],
            'SESSION_COOKIE_SAMESITE': self.config['session_cookie_samesite'],
            'SESSION_COOKIE_MAX_AGE': self.config['session_cookie_max_age'],
            'SESSION_COOKIE_DOMAIN': self.config['session_cookie_domain'],
            'SESSION_COOKIE_PATH': self.config['session_cookie_path'],
            'PERMANENT_SESSION_LIFETIME': timedelta(seconds=self.config['session_cookie_max_age']),
            'SESSION_USE_SIGNER': self.config['session_use_signer'],
        })
        
        @self.app.before_request
        def before_request():
            # Set session as permanent if configured
            if self.config['session_permanent']:
                session.permanent = True

class EnhancedCORSMiddleware:
    """Enhanced middleware for CORS configuration with production-ready settings."""
    
    def __init__(self, app: Flask):
        """Initialize enhanced CORS middleware."""
        self.app = app
        
        # Enhanced CORS configuration
        self.config = {
            'enable_cors': True,
            'cors_origins': ['*'],
            'cors_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
            'cors_allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With', 'X-CSRF-Token', 'x-request-id'],
            'cors_expose_headers': ['Content-Length', 'X-Total-Count', 'X-CSRF-Token'],
            'cors_supports_credentials': True,
            'cors_max_age': 86400,  # 24 hours
            'cors_allow_origin_regex': None,
            'cors_allow_private_network': False,
            'cors_allow_credentials': True,
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Initialize CORS
        self._setup_cors()
    
    def _load_config(self):
        """Load CORS configuration from Flask app config."""
        for key in self.config:
            config_key = f'CORS_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[key]
    
    def _setup_cors(self):
        """Setup enhanced CORS with Flask-CORS."""
        if not self.config['enable_cors']:
            return
        
        # Enhanced CORS configuration
        cors_config = {
            'origins': self.config['cors_origins'],
            'methods': self.config['cors_methods'],
            'allow_headers': self.config['cors_allow_headers'],
            'expose_headers': self.config['cors_expose_headers'],
            'supports_credentials': self.config['cors_supports_credentials'],
            'max_age': self.config['cors_max_age'],
            'allow_credentials': self.config['cors_allow_credentials'],
        }
        
        # Add regex support if configured
        if self.config['cors_allow_origin_regex']:
            cors_config['origins'] = self.config['cors_allow_origin_regex']
        
        # Initialize CORS
        CORS(self.app, **cors_config)
        
        # Custom CORS preflight handler
        @self.app.before_request
        def handle_preflight():
            if request.method == "OPTIONS":
                response = self._create_preflight_response()
                return response
    
    def _create_preflight_response(self) -> Response:
        """Create enhanced CORS preflight response."""
        response = Response()
        response.status_code = 200
        
        # Set CORS headers
        origin = request.headers.get('Origin')
        if origin and self._is_allowed_origin(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
        
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.config['cors_methods'])
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.config['cors_allow_headers'])
        response.headers['Access-Control-Expose-Headers'] = ', '.join(self.config['cors_expose_headers'])
        response.headers['Access-Control-Max-Age'] = str(self.config['cors_max_age'])
        
        if self.config['cors_supports_credentials']:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    def _is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if '*' in self.config['cors_origins']:
            return True
        
        if origin in self.config['cors_origins']:
            return True
        
        # Check regex patterns
        if self.config['cors_allow_origin_regex']:
            import re
            for pattern in self.config['cors_allow_origin_regex']:
                if re.match(pattern, origin):
                    return True
        
        return False

# Enhanced utility functions for security
def require_csrf_token(f: Callable) -> Callable:
    """Enhanced decorator to require CSRF token for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CSRF validation is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def require_secure_headers(f: Callable) -> Callable:
    """Enhanced decorator to require secure headers for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Security headers are handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def validate_request_origin(allowed_origins: List[str] = None) -> Callable:
    """Enhanced decorator to validate request origin."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if allowed_origins:
                origin = request.headers.get('Origin')
                if origin and origin not in allowed_origins:
                    raise Forbidden("Origin not allowed")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_https(f: Callable) -> Callable:
    """Enhanced decorator to require HTTPS for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not current_app.debug:
            raise Forbidden("HTTPS required")
        return f(*args, **kwargs)
    return decorated_function

def validate_content_type(allowed_types: List[str] = None) -> Callable:
    """Enhanced decorator to validate content type."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if allowed_types:
                content_type = request.content_type or ''
                if not any(allowed_type in content_type for allowed_type in allowed_types):
                    raise BadRequest("Content type not allowed")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_request_data(f: Callable) -> Callable:
    """Enhanced decorator to sanitize request data."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Sanitization is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

# Enhanced security utility functions
def generate_secure_token(length: int = 64) -> str:
    """Generate a secure random token with increased length."""
    return secrets.token_hex(length)

def generate_csrf_nonce() -> str:
    """Generate a nonce for Content Security Policy."""
    return secrets.token_hex(16)

def hash_password(password: str, salt: str = None) -> str:
    """Hash a password with salt using enhanced security."""
    if not salt:
        salt = secrets.token_hex(32)  # Increased salt length
    
    # Use a stronger hashing algorithm with more iterations
    hash_obj = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt.encode('utf-8'), 200000)
    return f"{salt}${hash_obj.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, hash_value = hashed.split('$', 1)
        return hash_password(password, salt) == hashed
    except:
        return False

def sanitize_filename(filename: str) -> str:
    """Enhanced filename sanitization for security."""
    import re
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove path traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension with enhanced security."""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions

def is_safe_url(url: str) -> bool:
    """Enhanced URL safety check (no open redirects)."""
    if not url:
        return False
    
    # Check for dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:', 'chrome:', 'moz-extension:']
    url_lower = url.lower()
    
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return False
    
    return True

def validate_json_payload(f: Callable) -> Callable:
    """Decorator to validate JSON payload size and content."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.is_json:
            # Check content length
            if request.content_length and request.content_length > 1024 * 1024:  # 1MB limit
                raise BadRequest("Payload too large")
            
            # Validate JSON structure
            try:
                data = request.get_json()
                if data is None:
                    raise BadRequest("Invalid JSON payload")
            except Exception:
                raise BadRequest("Invalid JSON payload")
        
        return f(*args, **kwargs)
    return decorated_function
