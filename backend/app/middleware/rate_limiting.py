"""
Rate Limiting Middleware

This module provides comprehensive rate limiting and throttling capabilities for API endpoints.
It includes per-endpoint, per-user, and per-IP rate limiting with configurable windows and limits.
"""

import time
import hashlib
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict, deque

from flask import Flask, Request, Response, request, jsonify, current_app, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import TooManyRequests

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app: Flask):
        """Initialize rate limiting middleware."""
        self.app = app
        self.rate_limit_cache = defaultdict(lambda: deque())
        self.user_rate_limit_cache = defaultdict(lambda: defaultdict(lambda: deque()))
        self.endpoint_rate_limit_cache = defaultdict(lambda: defaultdict(lambda: deque()))
        
        # Rate limiting configuration
        self.config = {
            'enable_rate_limiting': True,
            'enable_user_rate_limiting': True,
            'enable_endpoint_rate_limiting': True,
            'enable_ip_rate_limiting': True,
            'default_rate_limit': '100 per hour',
            'strict_rate_limiting': False,
            'log_rate_limit_violations': True,
            'return_rate_limit_headers': True,
            'rate_limit_storage': 'memory',  # memory, redis, database
            'cleanup_interval': 3600,  # seconds
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Initialize Flask-Limiter
        self.limiter = Limiter(
            app=app,
            key_func=self._get_rate_limit_key,
            default_limits=[self.config['default_rate_limit']],
            storage_uri=self._get_storage_uri(),
            strategy="fixed-window-2"
        )
        
        # Register with Flask app
        self._register_limiter()
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _load_config(self):
        """Load rate limiting configuration from Flask app config."""
        for key in self.config:
            config_key = f'RATE_LIMIT_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[config_key]
    
    def _get_storage_uri(self) -> str:
        """Get storage URI for rate limiting."""
        if self.config['rate_limit_storage'] == 'redis':
            redis_url = self.app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            return f"{redis_url}/rate_limiting"
        elif self.config['rate_limit_storage'] == 'database':
            return f"sqlite:///{self.app.config.get('RATE_LIMIT_DB', 'rate_limits.db')}"
        else:
            return "memory://"
    
    def _register_limiter(self):
        """Register rate limiter with Flask app."""
        # Global rate limiting
        @self.app.before_request
        def before_request():
            if not self.config['enable_rate_limiting']:
                return
            
            # Check global rate limits
            self._check_global_rate_limits()
            
            # Check IP-based rate limits
            if self.config['enable_ip_rate_limiting']:
                self._check_ip_rate_limits()
            
            # Check user-based rate limits
            if self.config['enable_user_rate_limiting']:
                self._check_user_rate_limits()
            
            # Check endpoint-based rate limits
            if self.config['enable_endpoint_rate_limiting']:
                self._check_endpoint_rate_limits()
        
        # Rate limit error handler
        @self.app.errorhandler(429)
        def ratelimit_handler(e):
            return self._create_rate_limit_response(e)
    
    def _get_rate_limit_key(self) -> str:
        """Get rate limit key for the current request."""
        # Try to get user ID from JWT token
        user_id = self._get_current_user_id()
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        return f"ip:{get_remote_address()}"
    
    def _get_current_user_id(self) -> Optional[str]:
        """Get current user ID from JWT token."""
        try:
            from flask_jwt_extended import get_jwt_identity
            return get_jwt_identity()
        except:
            return None
    
    def _check_global_rate_limits(self):
        """Check global rate limits."""
        key = "global"
        limit = self._parse_rate_limit(self.config['default_rate_limit'])
        
        if not self._is_within_rate_limit(key, limit):
            self._log_rate_limit_violation("global", key, limit)
            raise TooManyRequests("Global rate limit exceeded")
    
    def _check_ip_rate_limits(self):
        """Check IP-based rate limits."""
        ip = get_remote_address()
        key = f"ip:{ip}"
        
        # Different limits for different IP types
        if self._is_private_ip(ip):
            limit = self._parse_rate_limit("1000 per hour")  # More lenient for private IPs
        else:
            limit = self._parse_rate_limit("100 per hour")
        
        if not self._is_within_rate_limit(key, limit):
            self._log_rate_limit_violation("IP-based", key, limit)
            raise TooManyRequests("IP rate limit exceeded")
    
    def _check_user_rate_limits(self):
        """Check user-based rate limits."""
        user_id = self._get_current_user_id()
        if not user_id:
            return
        
        key = f"user:{user_id}"
        
        # Different limits for different user roles
        user_role = self._get_user_role(user_id)
        if user_role == 'admin':
            limit = self._parse_rate_limit("1000 per hour")
        elif user_role == 'manager':
            limit = self._parse_rate_limit("500 per hour")
        else:
            limit = self._parse_rate_limit("200 per hour")
        
        if not self._is_within_rate_limit(key, limit):
            self._log_rate_limit_violation("user-based", key, limit)
            raise TooManyRequests("User rate limit exceeded")
    
    def _check_endpoint_rate_limits(self):
        """Check endpoint-based rate limits."""
        endpoint = request.endpoint
        if not endpoint:
            return
        
        # Get endpoint-specific rate limits
        endpoint_limits = self._get_endpoint_rate_limits()
        if endpoint in endpoint_limits:
            key = f"endpoint:{endpoint}"
            limit = self._parse_rate_limit(endpoint_limits[endpoint])
            
            if not self._is_within_rate_limit(key, limit):
                self._log_rate_limit_violation("endpoint-based", key, limit)
                raise TooManyRequests("Endpoint rate limit exceeded")
    
    def _get_endpoint_rate_limits(self) -> Dict[str, str]:
        """Get endpoint-specific rate limits."""
        return {
            'auth.login': '5 per minute',
            'auth.register': '3 per hour',
            'auth.refresh': '10 per minute',
            'forms.create': '10 per hour',
            'forms.update': '20 per hour',
            'forms.delete': '5 per hour',
            'reports.export': '20 per hour',
            'files.upload': '50 per day',
            'files.download': '100 per hour',
            'users.create': '5 per day',
            'users.update': '20 per hour',
            'users.delete': '2 per day',
        }
    
    def _is_within_rate_limit(self, key: str, limit: Dict[str, Any]) -> bool:
        """Check if request is within rate limit."""
        now = time.time()
        window_start = now - limit['window']
        
        # Clean old entries
        while self.rate_limit_cache[key] and self.rate_limit_cache[key][0] < window_start:
            self.rate_limit_cache[key].popleft()
        
        # Check if limit exceeded
        if len(self.rate_limit_cache[key]) >= limit['max_requests']:
            return False
        
        # Add current request
        self.rate_limit_cache[key].append(now)
        return True
    
    def _parse_rate_limit(self, rate_limit: str) -> Dict[str, Any]:
        """Parse rate limit string into components."""
        parts = rate_limit.split()
        if len(parts) != 3 or parts[1] != 'per':
            raise ValueError(f"Invalid rate limit format: {rate_limit}")
        
        max_requests = int(parts[0])
        time_unit = parts[2]
        
        # Convert time unit to seconds
        time_multipliers = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400,
            'week': 604800,
            'month': 2592000,
            'year': 31536000
        }
        
        if time_unit not in time_multipliers:
            raise ValueError(f"Invalid time unit: {time_unit}")
        
        window = time_multipliers[time_unit]
        
        return {
            'max_requests': max_requests,
            'window': window,
            'time_unit': time_unit
        }
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP address is private."""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return False
    
    def _get_user_role(self, user_id: str) -> str:
        """Get user role for rate limiting purposes."""
        try:
            # This would typically query the database
            # For now, return a default role
            return 'user'
        except:
            return 'user'
    
    def _log_rate_limit_violation(self, limit_type: str, key: str, limit: Dict[str, Any]):
        """Log rate limit violation."""
        if self.config['log_rate_limit_violations']:
            logger.warning(
                f'Rate limit violation: {limit_type} limit exceeded for {key}. '
                f'Limit: {limit["max_requests"]} per {limit["time_unit"]}'
            )
    
    def _create_rate_limit_response(self, error: TooManyRequests) -> Tuple[Response, int]:
        """Create rate limit exceeded response."""
        response_data = {
            'success': False,
            'error': 'RATE_LIMIT_EXCEEDED',
            'message': 'Rate limit exceeded. Please try again later.',
            'timestamp': datetime.utcnow().isoformat(),
            'retry_after': self._get_retry_after(),
        }
        
        response = jsonify(response_data)
        response.status_code = 429
        
        # Add rate limit headers
        if self.config['return_rate_limit_headers']:
            response.headers['X-RateLimit-Limit'] = str(self._get_current_limit())
            response.headers['X-RateLimit-Remaining'] = str(self._get_remaining_requests())
            response.headers['X-RateLimit-Reset'] = str(self._get_reset_time())
            response.headers['Retry-After'] = str(self._get_retry_after())
        
        return response, 429
    
    def _get_retry_after(self) -> int:
        """Get retry after time in seconds."""
        # Default to 1 hour
        return 3600
    
    def _get_current_limit(self) -> int:
        """Get current rate limit."""
        # This would return the actual limit for the current request
        return 100
    
    def _get_remaining_requests(self) -> int:
        """Get remaining requests in current window."""
        # This would calculate remaining requests
        return 0
    
    def _get_reset_time(self) -> int:
        """Get reset time for current window."""
        # This would calculate when the window resets
        return int(time.time()) + 3600
    
    def _start_cleanup_task(self):
        """Start cleanup task for old rate limit entries."""
        def cleanup():
            while True:
                time.sleep(self.config['cleanup_interval'])
                self._cleanup_old_entries()
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_entries(self):
        """Clean up old rate limit entries."""
        now = time.time()
        max_age = 86400  # 24 hours
        
        for key in list(self.rate_limit_cache.keys()):
            # Remove entries older than max_age
            while self.rate_limit_cache[key] and self.rate_limit_cache[key][0] < (now - max_age):
                self.rate_limit_cache[key].popleft()
            
            # Remove empty keys
            if not self.rate_limit_cache[key]:
                del self.rate_limit_cache[key]

class ThrottleMiddleware:
    """Middleware for throttling requests based on various criteria."""
    
    def __init__(self, app: Flask):
        """Initialize throttle middleware."""
        self.app = app
        self.throttle_cache = defaultdict(lambda: deque())
        
        # Throttling configuration
        self.config = {
            'enable_throttling': True,
            'default_throttle_delay': 1.0,  # seconds
            'max_concurrent_requests': 10,
            'throttle_storage': 'memory',
            'log_throttling': True,
        }
        
        # Load configuration from app config
        self._load_config()
        
        # Register with Flask app
        self._register_throttler()
    
    def _load_config(self):
        """Load throttling configuration from Flask app config."""
        for key in self.config:
            config_key = f'THROTTLE_{key.upper()}'
            if config_key in self.app.config:
                self.config[key] = self.app.config[config_key]
    
    def _register_throttler(self):
        """Register throttle middleware with Flask app."""
        @self.app.before_request
        def before_request():
            if not self.config['enable_throttling']:
                return
            
            # Check concurrent request limits
            self._check_concurrent_requests()
            
            # Apply throttling delays
            self._apply_throttling()
    
    def _check_concurrent_requests(self):
        """Check concurrent request limits."""
        key = "concurrent"
        max_concurrent = self.config['max_concurrent_requests']
        
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Clean old entries
        while self.throttle_cache[key] and self.throttle_cache[key][0] < window_start:
            self.throttle_cache[key].popleft()
        
        # Check if limit exceeded
        if len(self.throttle_cache[key]) >= max_concurrent:
            raise TooManyRequests("Too many concurrent requests")
        
        # Add current request
        self.throttle_cache[key].append(now)
    
    def _apply_throttling(self):
        """Apply throttling delays."""
        # This would implement various throttling strategies
        # For now, just a basic delay
        time.sleep(self.config['default_throttle_delay'])

# Decorator functions for rate limiting
def rate_limit(limit: str, key_func: Optional[Callable] = None, 
               exempt_when: Optional[Callable] = None) -> Callable:
    """
    Decorator to apply rate limiting to a route.
    
    Args:
        limit: Rate limit string (e.g., "100 per hour")
        key_func: Function to generate rate limit key
        exempt_when: Function to determine when to exempt from rate limiting
    
    Returns:
        Decorated function with rate limiting
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if exempt from rate limiting
            if exempt_when and exempt_when():
                return func(*args, **kwargs)
            
            # Get rate limit key
            if key_func:
                rate_key = key_func()
            else:
                rate_key = f"route:{func.__name__}"
            
            # Apply rate limiting
            # This would integrate with the rate limiting system
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def throttle(delay: float = 1.0, max_concurrent: int = 5) -> Callable:
    """
    Decorator to apply throttling to a route.
    
    Args:
        delay: Delay between requests in seconds
        max_concurrent: Maximum concurrent requests allowed
    
    Returns:
        Decorated function with throttling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply throttling delay
            time.sleep(delay)
            
            # Check concurrent request limit
            # This would integrate with the throttling system
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def adaptive_rate_limit(base_limit: str, 
                       burst_limit: str = None,
                       adaptive_factor: float = 1.0) -> Callable:
    """
    Decorator to apply adaptive rate limiting based on system load.
    
    Args:
        base_limit: Base rate limit string
        burst_limit: Burst rate limit string
        adaptive_factor: Factor to adjust limits based on system load
    
    Returns:
        Decorated function with adaptive rate limiting
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current system load
            system_load = _get_system_load()
            
            # Adjust rate limit based on load
            adjusted_limit = _calculate_adjusted_limit(base_limit, system_load, adaptive_factor)
            
            # Apply adjusted rate limiting
            # This would integrate with the rate limiting system
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def _get_system_load() -> float:
    """Get current system load average."""
    try:
        import psutil
        return psutil.getloadavg()[0]
    except:
        return 1.0

def _calculate_adjusted_limit(base_limit: str, system_load: float, 
                            adaptive_factor: float) -> str:
    """Calculate adjusted rate limit based on system load."""
    # Parse base limit
    parts = base_limit.split()
    if len(parts) != 3:
        return base_limit
    
    max_requests = int(parts[0])
    time_unit = parts[2]
    
    # Adjust based on system load
    if system_load > 2.0:  # High load
        adjusted_requests = int(max_requests * 0.5)  # Reduce by 50%
    elif system_load > 1.0:  # Medium load
        adjusted_requests = int(max_requests * 0.8)  # Reduce by 20%
    else:  # Low load
        adjusted_requests = int(max_requests * adaptive_factor)
    
    return f"{adjusted_requests} per {time_unit}"
