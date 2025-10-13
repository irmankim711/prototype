"""
API Response Caching Middleware

Provides intelligent response caching for GET endpoints with:
- ETag-based caching for static resources and form definitions
- Cache headers optimization for different content types
- Cache invalidation hooks for data modifications
- Conditional request handling (If-None-Match, If-Modified-Since)
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from flask import request, Response, current_app, g, make_response, jsonify
import logging

logger = logging.getLogger(__name__)


class ResponseCacheMiddleware:
    """
    Middleware for caching API responses with intelligent cache control
    """
    
    def __init__(self, app=None):
        self.app = app
        self.cache_manager = None
        self.cache_config = {
            # Default cache settings by content type
            'application/json': {'ttl': 300, 'etag': True},
            'text/html': {'ttl': 600, 'etag': True},
            'text/css': {'ttl': 3600, 'etag': True},
            'application/javascript': {'ttl': 3600, 'etag': True},
            'image/*': {'ttl': 86400, 'etag': True},
            'application/pdf': {'ttl': 1800, 'etag': True}
        }
        
        # Endpoints that should be cached
        self.cacheable_endpoints = {
            '/api/forms': {'ttl': 300, 'etag': True, 'vary': ['user_id']},
            '/api/forms/<int:form_id>': {'ttl': 600, 'etag': True, 'vary': ['user_id']},
            '/api/templates': {'ttl': 1800, 'etag': True, 'vary': ['user_id']},
            '/api/templates/<template_id>': {'ttl': 3600, 'etag': True},
            '/api/reports': {'ttl': 180, 'etag': True, 'vary': ['user_id']},
            '/api/dashboard/stats': {'ttl': 300, 'etag': True, 'vary': ['user_id']},
            '/api/users/profile': {'ttl': 900, 'etag': True, 'vary': ['user_id']},
            '/api/public-forms/<access_key>': {'ttl': 1800, 'etag': True},
        }
        
        # Endpoints that should invalidate cache when modified
        self.invalidation_hooks = {
            'POST': ['/api/forms', '/api/templates', '/api/reports'],
            'PUT': ['/api/forms/*', '/api/templates/*', '/api/reports/*', '/api/users/profile'],
            'DELETE': ['/api/forms/*', '/api/templates/*', '/api/reports/*'],
            'PATCH': ['/api/forms/*', '/api/templates/*', '/api/reports/*', '/api/users/profile']
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        self.app = app
        
        # Get cache manager from app
        if hasattr(app, 'cache_manager'):
            self.cache_manager = app.cache_manager
        
        # Register middleware
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        logger.info("Response cache middleware initialized")
    
    def before_request(self):
        """Handle incoming requests for cache validation"""
        # Only process GET requests for caching
        if request.method != 'GET':
            return None
        
        # Check if endpoint is cacheable
        cache_config = self._get_cache_config_for_endpoint(request.endpoint, request.path)
        if not cache_config:
            return None
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        g.cache_key = cache_key
        g.cache_config = cache_config
        
        # Try to get cached response
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            # Check conditional headers
            if self._handle_conditional_request(cached_response):
                return cached_response['response']
        
        # Store start time for response time tracking
        g.request_start_time = time.time()
    
    def after_request(self, response: Response) -> Response:
        """Handle outgoing responses for caching"""
        # Handle cache invalidation for non-GET requests
        if request.method != 'GET':
            self._handle_cache_invalidation(request.method, request.path)
            return response
        
        # Only cache successful GET responses
        if not hasattr(g, 'cache_config') or response.status_code != 200:
            return response
        
        cache_config = g.cache_config
        cache_key = g.cache_key
        
        # Add cache headers
        self._add_cache_headers(response, cache_config)
        
        # Cache the response
        self._cache_response(cache_key, response, cache_config)
        
        return response
    
    def _get_cache_config_for_endpoint(self, endpoint: str, path: str) -> Optional[Dict[str, Any]]:
        """Get cache configuration for an endpoint"""
        # Check exact endpoint match
        if path in self.cacheable_endpoints:
            return self.cacheable_endpoints[path]
        
        # Check pattern matches
        for pattern, config in self.cacheable_endpoints.items():
            if self._path_matches_pattern(path, pattern):
                return config
        
        return None
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches a pattern with wildcards"""
        # Simple pattern matching for now
        if '<' in pattern and '>' in pattern:
            # Extract the base path
            base_pattern = pattern.split('<')[0].rstrip('/')
            return path.startswith(base_pattern)
        
        return path == pattern
    
    def _generate_cache_key(self, request) -> str:
        """Generate cache key for request"""
        key_parts = ['response_cache', request.method, request.path]
        
        # Add query parameters (sorted for consistency)
        if request.args:
            query_string = '&'.join(f"{k}={v}" for k, v in sorted(request.args.items()))
            key_parts.append(query_string)
        
        # Add user context if needed
        cache_config = getattr(g, 'cache_config', {})
        if 'user_id' in cache_config.get('vary', []):
            from ..decorators import get_current_user_id
            try:
                user_id = get_current_user_id()
                if user_id:
                    key_parts.append(f"user:{user_id}")
            except Exception:
                pass  # No user context available
        
        # Add Accept header for content negotiation
        accept_header = request.headers.get('Accept', '')
        if accept_header:
            accept_hash = hashlib.md5(accept_header.encode()).hexdigest()[:8]
            key_parts.append(f"accept:{accept_hash}")
        
        cache_key = ':'.join(key_parts)
        
        # Hash long keys
        if len(cache_key) > 250:
            cache_key = f"response_cache:hash:{hashlib.md5(cache_key.encode()).hexdigest()}"
        
        return cache_key
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response data"""
        if not self.cache_manager:
            return None
        
        try:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data and isinstance(cached_data, dict):
                return cached_data
        except Exception as e:
            logger.warning(f"Error retrieving cached response: {e}")
        
        return None
    
    def _handle_conditional_request(self, cached_response: Dict[str, Any]) -> bool:
        """Handle conditional requests (If-None-Match, If-Modified-Since)"""
        # Handle ETag validation
        if_none_match = request.headers.get('If-None-Match')
        if if_none_match and cached_response.get('etag'):
            if if_none_match == cached_response['etag'] or if_none_match == '*':
                # Return 304 Not Modified
                response = make_response('', 304)
                response.headers['ETag'] = cached_response['etag']
                if cached_response.get('last_modified'):
                    response.headers['Last-Modified'] = cached_response['last_modified']
                cached_response['response'] = response
                return True
        
        # Handle Last-Modified validation
        if_modified_since = request.headers.get('If-Modified-Since')
        if if_modified_since and cached_response.get('last_modified'):
            try:
                if_modified_time = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                last_modified_time = datetime.strptime(cached_response['last_modified'], '%a, %d %b %Y %H:%M:%S GMT')
                
                if last_modified_time <= if_modified_time:
                    # Return 304 Not Modified
                    response = make_response('', 304)
                    response.headers['Last-Modified'] = cached_response['last_modified']
                    if cached_response.get('etag'):
                        response.headers['ETag'] = cached_response['etag']
                    cached_response['response'] = response
                    return True
            except ValueError:
                pass  # Invalid date format
        
        return False
    
    def _add_cache_headers(self, response: Response, cache_config: Dict[str, Any]):
        """Add appropriate cache headers to response"""
        ttl = cache_config.get('ttl', 300)
        
        # Add Cache-Control header
        if ttl > 0:
            response.headers['Cache-Control'] = f'public, max-age={ttl}'
        else:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        # Add ETag if enabled
        if cache_config.get('etag', False) and response.data:
            etag = self._generate_etag(response.data)
            response.headers['ETag'] = etag
        
        # Add Last-Modified header
        last_modified = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        response.headers['Last-Modified'] = last_modified
        
        # Add Vary header for user-specific content
        vary_headers = cache_config.get('vary', [])
        if vary_headers:
            if 'user_id' in vary_headers:
                response.headers['Vary'] = 'Authorization'
        
        # Add Expires header
        if ttl > 0:
            expires = (datetime.utcnow() + timedelta(seconds=ttl)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            response.headers['Expires'] = expires
    
    def _generate_etag(self, data: bytes) -> str:
        """Generate ETag for response data"""
        return f'"{hashlib.md5(data).hexdigest()}"'
    
    def _cache_response(self, cache_key: str, response: Response, cache_config: Dict[str, Any]):
        """Cache the response data"""
        if not self.cache_manager:
            return
        
        try:
            ttl = cache_config.get('ttl', 300)
            if ttl <= 0:
                return  # Don't cache if TTL is 0 or negative
            
            # Prepare cached response data
            cached_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response.get_data().decode('utf-8') if response.get_data() else '',
                'content_type': response.content_type,
                'cached_at': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
            
            # Add ETag and Last-Modified if present
            if 'ETag' in response.headers:
                cached_data['etag'] = response.headers['ETag']
            if 'Last-Modified' in response.headers:
                cached_data['last_modified'] = response.headers['Last-Modified']
            
            # Cache the response
            self.cache_manager.set(cache_key, cached_data, ttl)
            
        except Exception as e:
            logger.warning(f"Error caching response: {e}")
    
    def _handle_cache_invalidation(self, method: str, path: str):
        """Handle cache invalidation for data modification requests"""
        if method not in self.invalidation_hooks:
            return
        
        patterns_to_invalidate = self.invalidation_hooks[method]
        
        for pattern in patterns_to_invalidate:
            if self._should_invalidate_for_path(path, pattern):
                self._invalidate_cache_pattern(pattern)
    
    def _should_invalidate_for_path(self, path: str, pattern: str) -> bool:
        """Check if path should trigger invalidation for pattern"""
        if pattern.endswith('*'):
            base_pattern = pattern[:-1]
            return path.startswith(base_pattern)
        
        return path == pattern
    
    def _invalidate_cache_pattern(self, pattern: str):
        """Invalidate cached responses matching pattern"""
        if not self.cache_manager:
            return
        
        try:
            # Convert pattern to cache key pattern
            if pattern.endswith('*'):
                cache_pattern = f"response_cache:GET:{pattern[:-1]}*"
            else:
                cache_pattern = f"response_cache:GET:{pattern}*"
            
            # Delete matching keys
            deleted_count = self.cache_manager.delete_pattern(cache_pattern)
            if deleted_count > 0:
                logger.info(f"Invalidated {deleted_count} cached responses for pattern: {pattern}")
                
        except Exception as e:
            logger.warning(f"Error invalidating cache pattern {pattern}: {e}")
    
    def invalidate_cache_for_user(self, user_id: str):
        """Invalidate all cached responses for a specific user"""
        if not self.cache_manager:
            return
        
        try:
            pattern = f"response_cache:*:user:{user_id}*"
            deleted_count = self.cache_manager.delete_pattern(pattern)
            if deleted_count > 0:
                logger.info(f"Invalidated {deleted_count} cached responses for user: {user_id}")
        except Exception as e:
            logger.warning(f"Error invalidating cache for user {user_id}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get response cache statistics"""
        if not self.cache_manager:
            return {'error': 'Cache manager not available'}
        
        try:
            # Get general cache stats
            stats = self.cache_manager.get_stats()
            
            # Add response cache specific stats
            pattern = "response_cache:*"
            if hasattr(self.cache_manager, 'redis_client') and self.cache_manager.redis_client:
                keys = self.cache_manager.redis_client.keys(pattern)
                stats['response_cache_keys'] = len(keys)
            
            return stats
            
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {'error': str(e)}


def cache_response(ttl: int = 300, etag: bool = True, vary: List[str] = None):
    """
    Decorator for caching specific endpoint responses
    
    Args:
        ttl: Time to live in seconds
        etag: Whether to generate ETag headers
        vary: List of headers to vary on (e.g., ['user_id'])
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set cache config in g for middleware to use
            g.cache_config = {
                'ttl': ttl,
                'etag': etag,
                'vary': vary or []
            }
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def no_cache(func: Callable):
    """Decorator to disable caching for specific endpoints"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        g.cache_config = {'ttl': 0}  # Disable caching
        return func(*args, **kwargs)
    
    return wrapper


# Global middleware instance
response_cache_middleware = ResponseCacheMiddleware()

def init_response_cache_middleware(app):
    """Initialize response cache middleware"""
    response_cache_middleware.init_app(app)
    app.response_cache_middleware = response_cache_middleware
    logger.info("Response cache middleware initialized")