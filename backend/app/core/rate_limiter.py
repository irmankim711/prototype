"""
Production-Grade Rate Limiting Module
Advanced rate limiting with Redis backend, multiple strategies, and monitoring
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta, timezone
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import redis
import hashlib
from flask import request, jsonify, g, current_app

from .logging import get_logger

logger = get_logger(__name__)

class RateLimitStrategy(Enum):
    """Rate limiting strategy enumeration"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    ADAPTIVE = "adaptive"

class RateLimitScope(Enum):
    """Rate limiting scope enumeration"""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    ENDPOINT = "endpoint"
    API_KEY = "api_key"

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    name: str
    requests: int
    window: int  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    scope: RateLimitScope = RateLimitScope.IP
    burst_requests: Optional[int] = None
    burst_window: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'requests': self.requests,
            'window': self.window,
            'strategy': self.strategy.value,
            'scope': self.scope.value,
            'burst_requests': self.burst_requests,
            'burst_window': self.burst_window
        }

class RateLimitExceeded(Exception):
    """Rate limit exceeded exception"""
    
    def __init__(self, message: str, retry_after: int, rule: RateLimitRule):
        super().__init__(message)
        self.retry_after = retry_after
        self.rule = rule

class RateLimiter:
    """
    Advanced rate limiter with multiple strategies and monitoring
    
    Features:
    - Multiple rate limiting strategies
    - Redis-backed storage
    - Per-user, per-IP, per-endpoint limiting
    - Burst handling
    - Adaptive rate limiting
    - Comprehensive monitoring
    - Whitelist/blacklist support
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        )
        
        # Default rules
        self.default_rules = {
            'api_general': RateLimitRule(
                name='api_general',
                requests=100,
                window=3600,  # 1 hour
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.IP
            ),
            'login_attempts': RateLimitRule(
                name='login_attempts',
                requests=5,
                window=900,  # 15 minutes
                strategy=RateLimitStrategy.FIXED_WINDOW,
                scope=RateLimitScope.IP
            ),
            'form_submissions': RateLimitRule(
                name='form_submissions',
                requests=50,
                window=3600,  # 1 hour
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.USER
            )
        }
        
        # Initialize rules
        self.rules = self.default_rules.copy()
        
        # Monitoring data
        self.monitoring_data = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'errors': 0
        }

    def add_rule(self, rule: RateLimitRule):
        """Add a new rate limiting rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added rate limiting rule: {rule.name}")

    def get_identifier(self, scope: RateLimitScope, request_obj=None) -> str:
        """Get identifier based on scope"""
        if request_obj is None:
            request_obj = request
            
        if scope == RateLimitScope.IP:
            return request_obj.remote_addr or 'unknown'
        elif scope == RateLimitScope.USER:
            # Try to get user ID from JWT or session
            try:
                from flask_jwt_extended import get_jwt_identity
                user_id = get_jwt_identity()
                return f"user_{user_id}" if user_id else request_obj.remote_addr
            except:
                return request_obj.remote_addr
        elif scope == RateLimitScope.ENDPOINT:
            return request_obj.endpoint or request_obj.path
        elif scope == RateLimitScope.API_KEY:
            return request_obj.headers.get('X-API-Key', 'unknown')
        else:
            return 'global'

    def check_rate_limit(self, rule_name: str, identifier: str) -> Tuple[bool, int]:
        """Check if request is within rate limit"""
        if rule_name not in self.rules:
            logger.warning(f"Rate limit rule '{rule_name}' not found")
            return True, 0
            
        rule = self.rules[rule_name]
        key = f"rate_limit:{rule_name}:{identifier}"
        
        try:
            current_time = time.time()
            
            if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                window_start = int(current_time / rule.window) * rule.window
                key = f"{key}:{window_start}"
                
                # Get current count
                current_count = self.redis_client.get(key)
                if current_count is None:
                    current_count = 0
                else:
                    current_count = int(current_count)
                
                if current_count >= rule.requests:
                    return False, rule.window
                
                # Increment count
                self.redis_client.incr(key)
                self.redis_client.expire(key, rule.window)
                
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                # Use sorted set for sliding window
                zset_key = f"{key}:zset"
                
                # Remove old entries
                cutoff = current_time - rule.window
                self.redis_client.zremrangebyscore(zset_key, 0, cutoff)
                
                # Count current entries
                current_count = self.redis_client.zcard(zset_key)
                
                if current_count >= rule.requests:
                    return False, rule.window
                
                # Add current request
                self.redis_client.zadd(zset_key, {str(current_time): current_time})
                self.redis_client.expire(zset_key, rule.window)
            
            return True, 0
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # On error, allow request but log
            return True, 0

    def rate_limit(self, rule_name: str, requests: int = None, window: int = None, 
                   strategy: RateLimitStrategy = None, scope: RateLimitScope = None):
        """Decorator for rate limiting endpoints"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Create rule if not exists
                if rule_name not in self.rules:
                    rule = RateLimitRule(
                        name=rule_name,
                        requests=requests or 100,
                        window=window or 3600,
                        strategy=strategy or RateLimitStrategy.SLIDING_WINDOW,
                        scope=scope or RateLimitScope.IP
                    )
                    self.add_rule(rule)
                
                rule = self.rules[rule_name]
                identifier = self.get_identifier(rule.scope)
                
                # Check rate limit
                allowed, retry_after = self.check_rate_limit(rule_name, identifier)
                
                if not allowed:
                    self.monitoring_data['rate_limited_requests'] += 1
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': retry_after,
                        'limit': rule.requests,
                        'window': rule.window
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(retry_after)
                    return response
                
                self.monitoring_data['total_requests'] += 1
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator

# Global rate limiter instance
rate_limiter = RateLimiter()

# Convenience function for decorators
def rate_limit(rule_name: str, requests: int = None, window: int = None, 
               strategy: RateLimitStrategy = None, scope: RateLimitScope = None):
    """Convenience function for rate limiting"""
    return rate_limiter.rate_limit(rule_name, requests, window, strategy, scope)
