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
from flask import request, jsonify, g

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
                scope=RateLimitScope.IP,
                burst_requests=10,
                burst_window=3600
            ),
            'form_submission': RateLimitRule(
                name='form_submission',
                requests=10,
                window=300,  # 5 minutes
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                scope=RateLimitScope.USER
            )
        }
        
        # Whitelist and blacklist
        self.whitelist = set()
        self.blacklist = set()
        
        # Monitoring metrics
        self.metrics = {
            'total_requests': 0,
            'allowed_requests': 0,
            'blocked_requests': 0,
            'rules_triggered': {},
            'start_time': datetime.now(timezone.utc).isoformat()
        }
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load rate limiting configuration"""
        try:
            # Load whitelist
            whitelist_str = os.getenv('RATE_LIMIT_WHITELIST', '')
            if whitelist_str:
                self.whitelist.update(whitelist_str.split(','))
            
            # Load blacklist
            blacklist_str = os.getenv('RATE_LIMIT_BLACKLIST', '')
            if blacklist_str:
                self.blacklist.update(blacklist_str.split(','))
            
            logger.info(f"Rate limiter configured with {len(self.whitelist)} whitelisted and {len(self.blacklist)} blacklisted entries")
            
        except Exception as e:
            logger.error(f"Failed to load rate limiting config: {str(e)}")
    
    def add_rule(self, rule: RateLimitRule):
        """Add a rate limiting rule"""
        self.default_rules[rule.name] = rule
        logger.info(f"Added rate limiting rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove a rate limiting rule"""
        if rule_name in self.default_rules:
            del self.default_rules[rule_name]
            logger.info(f"Removed rate limiting rule: {rule_name}")
    
    def whitelist_add(self, identifier: str):
        """Add identifier to whitelist"""
        self.whitelist.add(identifier)
        logger.info(f"Added {identifier} to rate limit whitelist")
    
    def blacklist_add(self, identifier: str):
        """Add identifier to blacklist"""
        self.blacklist.add(identifier)
        logger.info(f"Added {identifier} to rate limit blacklist")
    
    def check_limit(
        self,
        rule_name: str,
        identifier: Optional[str] = None,
        custom_rule: Optional[RateLimitRule] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        
        Args:
            rule_name: Name of the rule to apply
            identifier: Unique identifier for the requester
            custom_rule: Custom rule to use instead of default
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            self.metrics['total_requests'] += 1
            
            # Get rule
            rule = custom_rule or self.default_rules.get(rule_name)
            if not rule:
                logger.warning(f"Rate limit rule '{rule_name}' not found")
                return True, {}
            
            # Get identifier
            if not identifier:
                identifier = self._get_identifier(rule.scope)
            
            # Check whitelist/blacklist
            if identifier in self.whitelist:
                self.metrics['allowed_requests'] += 1
                return True, {'whitelisted': True}
            
            if identifier in self.blacklist:
                self.metrics['blocked_requests'] += 1
                return False, {
                    'blacklisted': True,
                    'retry_after': rule.window
                }
            
            # Apply rate limiting strategy
            if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                allowed, info = self._check_fixed_window(rule, identifier)
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                allowed, info = self._check_sliding_window(rule, identifier)
            elif rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                allowed, info = self._check_token_bucket(rule, identifier)
            elif rule.strategy == RateLimitStrategy.ADAPTIVE:
                allowed, info = self._check_adaptive(rule, identifier)
            else:
                allowed, info = self._check_fixed_window(rule, identifier)
            
            # Update metrics
            if allowed:
                self.metrics['allowed_requests'] += 1
            else:
                self.metrics['blocked_requests'] += 1
                rule_key = f"{rule_name}_{rule.strategy.value}"
                self.metrics['rules_triggered'][rule_key] = self.metrics['rules_triggered'].get(rule_key, 0) + 1
            
            # Add rule info
            info.update({
                'rule_name': rule_name,
                'strategy': rule.strategy.value,
                'scope': rule.scope.value,
                'identifier': identifier
            })
            
            return allowed, info
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Fail open - allow request if rate limiting fails
            return True, {'error': str(e)}
    
    def _get_identifier(self, scope: RateLimitScope) -> str:
        """Get identifier based on scope"""
        try:
            if scope == RateLimitScope.IP:
                return request.remote_addr or 'unknown'
            elif scope == RateLimitScope.USER:
                user = getattr(g, 'current_user', None)
                return user.id if user else request.remote_addr or 'anonymous'
            elif scope == RateLimitScope.ENDPOINT:
                return f"{request.method}:{request.endpoint or request.path}"
            elif scope == RateLimitScope.API_KEY:
                api_key = request.headers.get('X-API-Key')
                return api_key or request.remote_addr or 'no_api_key'
            else:
                return 'global'
        except Exception:
            return 'unknown'
    
    def _check_fixed_window(self, rule: RateLimitRule, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Fixed window rate limiting"""
        current_time = int(time.time())
        window_start = (current_time // rule.window) * rule.window
        
        key = f"rate_limit:fixed:{rule.name}:{identifier}:{window_start}"
        
        try:
            current_count = self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= rule.requests:
                time_remaining = rule.window - (current_time - window_start)
                return False, {
                    'current_count': current_count,
                    'limit': rule.requests,
                    'window': rule.window,
                    'retry_after': time_remaining,
                    'reset_time': window_start + rule.window
                }
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, rule.window)
            pipe.execute()
            
            return True, {
                'current_count': current_count + 1,
                'limit': rule.requests,
                'window': rule.window,
                'remaining': rule.requests - current_count - 1
            }
            
        except Exception as e:
            logger.error(f"Fixed window rate limit check failed: {str(e)}")
            return True, {'error': str(e)}
    
    def _check_sliding_window(self, rule: RateLimitRule, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiting"""
        current_time = time.time()
        window_start = current_time - rule.window
        
        key = f"rate_limit:sliding:{rule.name}:{identifier}"
        
        try:
            # Remove old entries and count current requests
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.expire(key, rule.window)
            results = pipe.execute()
            
            current_count = results[1] if len(results) > 1 else 0
            
            if current_count >= rule.requests:
                # Get oldest entry to calculate retry time
                oldest_entries = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_time = oldest_entries[0][1]
                    retry_after = int(oldest_time + rule.window - current_time)
                else:
                    retry_after = rule.window
                
                return False, {
                    'current_count': current_count,
                    'limit': rule.requests,
                    'window': rule.window,
                    'retry_after': max(retry_after, 1)
                }
            
            # Add current request
            self.redis_client.zadd(key, {f"{current_time}:{hash(identifier)}": current_time})
            
            return True, {
                'current_count': current_count + 1,
                'limit': rule.requests,
                'window': rule.window,
                'remaining': rule.requests - current_count - 1
            }
            
        except Exception as e:
            logger.error(f"Sliding window rate limit check failed: {str(e)}")
            return True, {'error': str(e)}
    
    def _check_token_bucket(self, rule: RateLimitRule, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiting"""
        current_time = time.time()
        key = f"rate_limit:bucket:{rule.name}:{identifier}"
        
        try:
            # Get current bucket state
            bucket_data = self.redis_client.get(key)
            
            if bucket_data:
                try:
                    bucket_info = json.loads(bucket_data.decode() if isinstance(bucket_data, bytes) else bucket_data)
                    tokens = bucket_info.get('tokens', rule.requests)
                    last_refill = bucket_info.get('last_refill', current_time)
                except (json.JSONDecodeError, KeyError):
                    tokens = rule.requests
                    last_refill = current_time
            else:
                tokens = rule.requests
                last_refill = current_time
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            refill_rate = rule.requests / rule.window
            tokens_to_add = int(time_elapsed * refill_rate)
            tokens = min(rule.requests, tokens + tokens_to_add)
            
            if tokens < 1:
                retry_after = int((1 - tokens) / refill_rate)
                return False, {
                    'tokens': tokens,
                    'limit': rule.requests,
                    'refill_rate': refill_rate,
                    'retry_after': retry_after
                }
            
            # Consume one token
            tokens -= 1
            
            # Update bucket state
            bucket_info = {
                'tokens': tokens,
                'last_refill': current_time
            }
            self.redis_client.setex(key, rule.window * 2, json.dumps(bucket_info))
            
            return True, {
                'tokens': tokens,
                'limit': rule.requests,
                'refill_rate': refill_rate
            }
            
        except Exception as e:
            logger.error(f"Token bucket rate limit check failed: {str(e)}")
            return True, {'error': str(e)}
    
    def _check_adaptive(self, rule: RateLimitRule, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Adaptive rate limiting based on system load"""
        # Simple adaptive implementation - adjust based on Redis response time
        start_time = time.time()
        
        # Measure Redis latency
        try:
            self.redis_client.ping()
            latency = (time.time() - start_time) * 1000  # ms
        except Exception:
            latency = 100  # Default high latency
        
        # Adjust rate limit based on latency
        if latency > 50:  # High latency
            adjusted_requests = max(1, rule.requests // 2)
        elif latency > 20:  # Medium latency
            adjusted_requests = max(1, int(rule.requests * 0.75))
        else:  # Low latency
            adjusted_requests = rule.requests
        
        # Use sliding window with adjusted limit
        adjusted_rule = RateLimitRule(
            name=rule.name,
            requests=adjusted_requests,
            window=rule.window,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            scope=rule.scope
        )
        
        allowed, info = self._check_sliding_window(adjusted_rule, identifier)
        info['adaptive'] = True
        info['system_latency'] = latency
        info['adjusted_limit'] = adjusted_requests
        info['original_limit'] = rule.requests
        
        return allowed, info
    
    def get_rate_limit_info(self, rule_name: str, identifier: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit information without consuming quota"""
        try:
            rule = self.default_rules.get(rule_name)
            if not rule:
                return {}
            
            if not identifier:
                identifier = self._get_identifier(rule.scope)
            
            if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                current_time = int(time.time())
                window_start = (current_time // rule.window) * rule.window
                key = f"rate_limit:fixed:{rule.name}:{identifier}:{window_start}"
                current_count = self.redis_client.get(key)
                current_count = int(current_count) if current_count else 0
                
                return {
                    'current_count': current_count,
                    'limit': rule.requests,
                    'remaining': max(0, rule.requests - current_count),
                    'reset_time': window_start + rule.window
                }
            
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                current_time = time.time()
                window_start = current_time - rule.window
                key = f"rate_limit:sliding:{rule.name}:{identifier}"
                
                # Count current requests in window
                current_count = self.redis_client.zcount(key, window_start, current_time)
                
                return {
                    'current_count': current_count,
                    'limit': rule.requests,
                    'remaining': max(0, rule.requests - current_count),
                    'window': rule.window
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get rate limit info: {str(e)}")
            return {}
    
    def reset_limit(self, rule_name: str, identifier: Optional[str] = None):
        """Reset rate limit for an identifier"""
        try:
            rule = self.default_rules.get(rule_name)
            if not rule:
                return False
            
            if not identifier:
                identifier = self._get_identifier(rule.scope)
            
            # Delete all keys for this rule and identifier
            pattern = f"rate_limit:*:{rule.name}:{identifier}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            logger.info(f"Reset rate limit for rule '{rule_name}' and identifier '{identifier}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {str(e)}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        total_requests = max(self.metrics['total_requests'], 1)
        
        return {
            **self.metrics,
            'allowed_percentage': (self.metrics['allowed_requests'] / total_requests) * 100,
            'blocked_percentage': (self.metrics['blocked_requests'] / total_requests) * 100,
            'whitelist_size': len(self.whitelist),
            'blacklist_size': len(self.blacklist),
            'active_rules': len(self.default_rules),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def rate_limit(
    rule_name: str,
    requests: Optional[int] = None,
    window: Optional[int] = None,
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
    scope: RateLimitScope = RateLimitScope.IP
):
    """
    Decorator for rate limiting endpoints
    
    Args:
        rule_name: Name of the rate limiting rule
        requests: Number of requests allowed
        window: Time window in seconds
        strategy: Rate limiting strategy
        scope: Rate limiting scope
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter = get_rate_limiter()
            
            # Create custom rule if parameters provided
            custom_rule = None
            if requests and window:
                custom_rule = RateLimitRule(
                    name=rule_name,
                    requests=requests,
                    window=window,
                    strategy=strategy,
                    scope=scope
                )
            
            # Check rate limit
            allowed, info = limiter.check_limit(rule_name, custom_rule=custom_rule)
            
            if not allowed:
                response = {
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again in {info.get("retry_after", 60)} seconds.',
                    'rate_limit': info
                }
                
                resp = jsonify(response)
                resp.status_code = 429
                resp.headers['Retry-After'] = str(info.get('retry_after', 60))
                
                # Add rate limit headers
                if 'limit' in info:
                    resp.headers['X-RateLimit-Limit'] = str(info['limit'])
                if 'current_count' in info:
                    resp.headers['X-RateLimit-Remaining'] = str(max(0, info.get('limit', 0) - info['current_count']))
                if 'reset_time' in info:
                    resp.headers['X-RateLimit-Reset'] = str(info['reset_time'])
                
                return resp
            
            # Add rate limit headers to successful responses
            response = f(*args, **kwargs)
            if hasattr(response, 'headers') and 'limit' in info:
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                if 'remaining' in info:
                    response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                if 'reset_time' in info:
                    response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
            
            return response
        
        return decorated_function
    return decorator
