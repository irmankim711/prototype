"""
Redis Caching Infrastructure with Clustering Support

This module provides a comprehensive caching solution with:
- Redis clustering support
- Multi-level caching strategy
- TTL management
- Cache warming utilities
- Smart invalidation
- Performance monitoring
"""

import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app
import pickle
import time

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Centralized cache manager with Redis clustering support and intelligent caching strategies.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.redis_client = None
        self.redis_cluster = None
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize cache manager with Flask app"""
        self.app = app
        
        # Redis configuration
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        redis_cluster_nodes = app.config.get('REDIS_CLUSTER_NODES', [])
        
        try:
            if redis_cluster_nodes:
                # Use Redis Cluster if nodes are configured
                from rediscluster import RedisCluster
                self.redis_cluster = RedisCluster(
                    startup_nodes=redis_cluster_nodes,
                    decode_responses=False,
                    skip_full_coverage_check=True,
                    health_check_interval=30
                )
                self.redis_client = self.redis_cluster
                logger.info("Redis Cluster initialized successfully")
            else:
                # Use single Redis instance with connection pooling
                pool = redis.ConnectionPool.from_url(
                    redis_url,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                self.redis_client = redis.Redis(connection_pool=pool, decode_responses=False)
                logger.info("Redis single instance initialized successfully")
                
            # Test connection
            self.redis_client.ping()
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, identifier: Union[str, int], version: str = None) -> str:
        """Generate a consistent cache key with optional versioning"""
        key_parts = [prefix, str(identifier)]
        if version:
            key_parts.append(version)
        
        key = ":".join(key_parts)
        
        # Hash long keys to prevent Redis key length issues
        if len(key) > 250:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{prefix}:hash:{key_hash}"
        
        return key
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        try:
            # Use pickle for complex Python objects, JSON for simple types
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                return json.dumps(data, default=str).encode('utf-8')
            else:
                return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Failed to serialize data: {e}")
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from Redis storage"""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Failed to deserialize data: {e}")
                return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if not self.redis_client:
            return default
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                self.cache_stats['misses'] += 1
                return default
            
            self.cache_stats['hits'] += 1
            return self._deserialize_data(data)
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            serialized_data = self._serialize_data(value)
            result = self.redis_client.setex(key, ttl, serialized_data)
            self.cache_stats['sets'] += 1
            return result
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            self.cache_stats['deletes'] += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.cache_stats['deletes'] += deleted
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
            self.cache_stats['errors'] += 1
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get TTL for key (-1 if no expiry, -2 if key doesn't exist)"""
        if not self.redis_client:
            return -2
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2
    
    def extend_ttl(self, key: str, ttl: int) -> bool:
        """Extend TTL for existing key"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache extend TTL error for key {key}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.cache_stats.copy()
        
        # Calculate hit rate
        total_requests = stats['hits'] + stats['misses']
        stats['hit_rate'] = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Add Redis info if available
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats['redis_memory_used'] = redis_info.get('used_memory_human', 'N/A')
                stats['redis_connected_clients'] = redis_info.get('connected_clients', 0)
                stats['redis_keyspace_hits'] = redis_info.get('keyspace_hits', 0)
                stats['redis_keyspace_misses'] = redis_info.get('keyspace_misses', 0)
            except Exception as e:
                logger.error(f"Failed to get Redis info: {e}")
        
        return stats
    
    def clear_stats(self):
        """Clear cache statistics"""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        health = {
            'status': 'unhealthy',
            'redis_connected': False,
            'response_time_ms': None,
            'error': None
        }
        
        if not self.redis_client:
            health['error'] = 'Redis client not initialized'
            return health
        
        try:
            start_time = time.time()
            self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            
            health.update({
                'status': 'healthy',
                'redis_connected': True,
                'response_time_ms': round(response_time, 2)
            })
            
        except Exception as e:
            health['error'] = str(e)
        
        return health


class FormCacheManager:
    """Specialized cache manager for form definitions with smart invalidation"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = "form"
        self.default_ttl = 1800  # 30 minutes
    
    def get_form_definition(self, form_id: int) -> Optional[Dict]:
        """Get cached form definition"""
        key = self.cache._generate_cache_key(self.prefix, f"def:{form_id}")
        return self.cache.get(key)
    
    def set_form_definition(self, form_id: int, form_data: Dict, ttl: int = None) -> bool:
        """Cache form definition with version-based key"""
        ttl = ttl or self.default_ttl
        
        # Add version to form data for cache invalidation
        form_data['_cached_at'] = datetime.utcnow().isoformat()
        form_data['_cache_version'] = form_data.get('updated_at', datetime.utcnow().isoformat())
        
        key = self.cache._generate_cache_key(self.prefix, f"def:{form_id}")
        return self.cache.set(key, form_data, ttl)
    
    def invalidate_form(self, form_id: int):
        """Invalidate all cached data for a form"""
        patterns = [
            f"{self.prefix}:def:{form_id}",
            f"{self.prefix}:schema:{form_id}",
            f"{self.prefix}:settings:{form_id}",
            f"{self.prefix}:submissions:{form_id}:*"
        ]
        
        for pattern in patterns:
            self.cache.delete_pattern(pattern)
    
    def get_form_schema(self, form_id: int) -> Optional[Dict]:
        """Get cached form schema"""
        key = self.cache._generate_cache_key(self.prefix, f"schema:{form_id}")
        return self.cache.get(key)
    
    def set_form_schema(self, form_id: int, schema: Dict, ttl: int = None) -> bool:
        """Cache form schema"""
        ttl = ttl or self.default_ttl
        key = self.cache._generate_cache_key(self.prefix, f"schema:{form_id}")
        return self.cache.set(key, schema, ttl)
    
    def get_form_submissions_count(self, form_id: int) -> Optional[int]:
        """Get cached form submissions count"""
        key = self.cache._generate_cache_key(self.prefix, f"submissions:count:{form_id}")
        return self.cache.get(key)
    
    def set_form_submissions_count(self, form_id: int, count: int, ttl: int = 300) -> bool:
        """Cache form submissions count (shorter TTL as it changes frequently)"""
        key = self.cache._generate_cache_key(self.prefix, f"submissions:count:{form_id}")
        return self.cache.set(key, count, ttl)


class UserCacheManager:
    """Specialized cache manager for user permissions and roles with session-based invalidation"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = "user"
        self.default_ttl = 900  # 15 minutes
    
    def get_user_permissions(self, user_id: int) -> Optional[List[str]]:
        """Get cached user permissions"""
        key = self.cache._generate_cache_key(self.prefix, f"perms:{user_id}")
        return self.cache.get(key)
    
    def set_user_permissions(self, user_id: int, permissions: List[str], ttl: int = None) -> bool:
        """Cache user permissions"""
        ttl = ttl or self.default_ttl
        key = self.cache._generate_cache_key(self.prefix, f"perms:{user_id}")
        return self.cache.set(key, permissions, ttl)
    
    def get_user_role(self, user_id: int) -> Optional[str]:
        """Get cached user role"""
        key = self.cache._generate_cache_key(self.prefix, f"role:{user_id}")
        return self.cache.get(key)
    
    def set_user_role(self, user_id: int, role: str, ttl: int = None) -> bool:
        """Cache user role"""
        ttl = ttl or self.default_ttl
        key = self.cache._generate_cache_key(self.prefix, f"role:{user_id}")
        return self.cache.set(key, role, ttl)
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get cached user profile"""
        key = self.cache._generate_cache_key(self.prefix, f"profile:{user_id}")
        return self.cache.get(key)
    
    def set_user_profile(self, user_id: int, profile: Dict, ttl: int = None) -> bool:
        """Cache user profile"""
        ttl = ttl or self.default_ttl
        key = self.cache._generate_cache_key(self.prefix, f"profile:{user_id}")
        return self.cache.set(key, profile, ttl)
    
    def invalidate_user(self, user_id: int):
        """Invalidate all cached data for a user (called on role/permission changes)"""
        patterns = [
            f"{self.prefix}:perms:{user_id}",
            f"{self.prefix}:role:{user_id}",
            f"{self.prefix}:profile:{user_id}",
            f"{self.prefix}:session:{user_id}:*"
        ]
        
        for pattern in patterns:
            self.cache.delete_pattern(pattern)
    
    def invalidate_user_session(self, user_id: int, session_id: str = None):
        """Invalidate user session cache"""
        if session_id:
            key = self.cache._generate_cache_key(self.prefix, f"session:{user_id}:{session_id}")
            self.cache.delete(key)
        else:
            pattern = f"{self.prefix}:session:{user_id}:*"
            self.cache.delete_pattern(pattern)


class ReportTemplateCacheManager:
    """Specialized cache manager for report templates with version-based cache keys"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = "template"
        self.default_ttl = 3600  # 1 hour (templates change less frequently)
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get cached report template"""
        key = self.cache._generate_cache_key(self.prefix, template_id)
        return self.cache.get(key)
    
    def set_template(self, template_id: str, template_data: Dict, ttl: int = None) -> bool:
        """Cache report template with version-based key"""
        ttl = ttl or self.default_ttl
        
        # Add version info for cache invalidation
        template_data['_cached_at'] = datetime.utcnow().isoformat()
        version = template_data.get('updated_at', datetime.utcnow().isoformat())
        
        key = self.cache._generate_cache_key(self.prefix, template_id, version)
        
        # Also cache without version for quick access
        key_no_version = self.cache._generate_cache_key(self.prefix, template_id)
        
        # Set both keys
        result1 = self.cache.set(key, template_data, ttl)
        result2 = self.cache.set(key_no_version, template_data, ttl)
        
        return result1 and result2
    
    def get_template_list(self, user_id: int = None, category: str = None) -> Optional[List[Dict]]:
        """Get cached template list"""
        cache_key_parts = ["list"]
        if user_id:
            cache_key_parts.append(f"user:{user_id}")
        if category:
            cache_key_parts.append(f"cat:{category}")
        
        key = self.cache._generate_cache_key(self.prefix, ":".join(cache_key_parts))
        return self.cache.get(key)
    
    def set_template_list(self, templates: List[Dict], user_id: int = None, category: str = None, ttl: int = 600) -> bool:
        """Cache template list (shorter TTL as lists change more frequently)"""
        cache_key_parts = ["list"]
        if user_id:
            cache_key_parts.append(f"user:{user_id}")
        if category:
            cache_key_parts.append(f"cat:{category}")
        
        key = self.cache._generate_cache_key(self.prefix, ":".join(cache_key_parts))
        return self.cache.set(key, templates, ttl)
    
    def invalidate_template(self, template_id: str):
        """Invalidate cached template and related lists"""
        # Delete specific template
        pattern = f"{self.prefix}:{template_id}*"
        self.cache.delete_pattern(pattern)
        
        # Delete template lists (they need to be refreshed)
        list_pattern = f"{self.prefix}:list*"
        self.cache.delete_pattern(list_pattern)
    
    def invalidate_template_lists(self):
        """Invalidate all template lists (called when templates are added/removed)"""
        pattern = f"{self.prefix}:list*"
        self.cache.delete_pattern(pattern)


def cache_result(key_prefix: str, ttl: int = 300, version_key: str = None):
    """
    Decorator for caching function results
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        version_key: Key in kwargs to use for versioning
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager from current app
            cache_manager = getattr(current_app, 'cache_manager', None)
            if not cache_manager:
                return func(*args, **kwargs)
            
            # Generate cache key from function arguments
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            for arg in args:
                if isinstance(arg, (str, int)):
                    key_parts.append(str(arg))
            
            # Add relevant kwargs to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, bool)):
                    key_parts.append(f"{k}:{v}")
            
            # Add version if specified
            version = None
            if version_key and version_key in kwargs:
                version = str(kwargs[version_key])
            
            cache_key = cache_manager._generate_cache_key(":".join(key_parts), "", version)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache manager instance
cache_manager = CacheManager()

# Specialized cache managers
form_cache = None
user_cache = None
template_cache = None

def init_cache_managers(app):
    """Initialize all cache managers"""
    global cache_manager, form_cache, user_cache, template_cache
    
    cache_manager.init_app(app)
    app.cache_manager = cache_manager
    
    # Initialize specialized cache managers
    form_cache = FormCacheManager(cache_manager)
    user_cache = UserCacheManager(cache_manager)
    template_cache = ReportTemplateCacheManager(cache_manager)
    
    app.form_cache = form_cache
    app.user_cache = user_cache
    app.template_cache = template_cache
    
    logger.info("Cache managers initialized successfully")