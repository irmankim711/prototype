"""
Data Source Manager

Central orchestration service for all data source operations.
Manages service registration, routing, caching, and provides a unified interface.

Enhanced with performance optimizations:
- Intelligent caching with cache warming
- Cache hit/miss metrics and monitoring
- Smart cache invalidation based on data source updates
"""

from typing import Dict, List, Any, Optional, Type
from datetime import datetime, timedelta
import logging
import redis
import json
import hashlib
import time
from flask import current_app

from .base_service import BaseDataSourceService, DataSourceResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataSourceManager:
    """
    Central manager for all data source services.
    
    Handles service registration, request routing, caching, and provides
    a unified interface for all data source operations.
    
    Enhanced with performance optimizations:
    - Intelligent caching with cache warming
    - Cache hit/miss metrics and monitoring
    - Smart cache invalidation based on data source updates
    """

    def __init__(self):
        self._services: Dict[str, BaseDataSourceService] = {}
        self._cache = None
        self._cache_ttl = 300  # 5 minutes default TTL
        self.logger = logger
        
        # Cache performance metrics
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0,
            'errors': 0,
            'warming_operations': 0
        }
        
        # Cache warming configuration
        self._warm_cache_sources = set()  # Sources to warm on startup
        self._cache_warming_enabled = True
        
        # Cache invalidation tracking
        self._source_versions = {}  # Track source data versions for smart invalidation

    def register_service(self, service: BaseDataSourceService) -> None:
        """
        Register a data source service.
        
        Args:
            service: Instance of a data source service
        """
        service_name = service.service_name
        self._services[service_name] = service
        self.logger.info(f"Registered data source service: {service_name}")

    def get_service_for_source(self, source_id: str) -> Optional[BaseDataSourceService]:
        """
        Find the appropriate service for a given source ID.
        
        Args:
            source_id: The data source identifier
            
        Returns:
            The service that can handle this source, or None if not found
        """
        for service in self._services.values():
            if service.supports_source(source_id):
                return service
        
        self.logger.warning(f"No service found for source ID: {source_id}")
        return None

    def get_data(self, source_id: str, params: Optional[Dict[str, Any]] = None) -> DataSourceResponse:
        """
        Get data from a data source with caching support.
        
        Args:
            source_id: Unique identifier for the data source
            params: Optional parameters for filtering, pagination, etc.
            
        Returns:
            DataSourceResponse with data or error information
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key('data', source_id, params)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for data request: {source_id}")
                return cached_response

            # Find appropriate service
            service = self.get_service_for_source(source_id)
            if not service:
                return self._create_error_response(
                    'DATA_SOURCE_NOT_FOUND',
                    f'No service available for data source: {source_id}',
                    {'source_id': source_id, 'available_services': list(self._services.keys())}
                )

            # Get data from service
            response = service.get_data(source_id, params)
            
            # Cache successful responses
            if response.success:
                self._set_cache(cache_key, response, ttl=self._cache_ttl)
                
            return response

        except Exception as e:
            self.logger.error(f"Error getting data for source {source_id}: {str(e)}")
            return self._create_error_response(
                'INTERNAL_ERROR',
                f'Internal error retrieving data: {str(e)}',
                {'source_id': source_id}
            )

    def get_fields(self, source_id: str) -> DataSourceResponse:
        """
        Get field definitions for a data source with caching.
        
        Args:
            source_id: Unique identifier for the data source
            
        Returns:
            DataSourceResponse with field definitions
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key('fields', source_id)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for fields request: {source_id}")
                return cached_response

            # Find appropriate service
            service = self.get_service_for_source(source_id)
            if not service:
                return self._create_error_response(
                    'DATA_SOURCE_NOT_FOUND',
                    f'No service available for data source: {source_id}',
                    {'source_id': source_id}
                )

            # Get fields from service
            response = service.get_fields(source_id)
            
            # Cache successful responses with longer TTL for fields
            if response.success:
                self._set_cache(cache_key, response, ttl=self._cache_ttl * 2)
                
            return response

        except Exception as e:
            self.logger.error(f"Error getting fields for source {source_id}: {str(e)}")
            return self._create_error_response(
                'INTERNAL_ERROR',
                f'Internal error retrieving fields: {str(e)}',
                {'source_id': source_id}
            )

    def get_preview(self, source_id: str, limit: int = 10) -> DataSourceResponse:
        """
        Get a preview sample of data from a source.
        
        Args:
            source_id: Unique identifier for the data source
            limit: Maximum number of records to return
            
        Returns:
            DataSourceResponse with sample data
        """
        try:
            service = self.get_service_for_source(source_id)
            if not service:
                return self._create_error_response(
                    'DATA_SOURCE_NOT_FOUND',
                    f'No service available for data source: {source_id}',
                    {'source_id': source_id}
                )

            return service.get_preview(source_id, limit)

        except Exception as e:
            self.logger.error(f"Error getting preview for source {source_id}: {str(e)}")
            return self._create_error_response(
                'INTERNAL_ERROR',
                f'Internal error retrieving preview: {str(e)}',
                {'source_id': source_id}
            )

    def refresh_data(self, source_id: str) -> DataSourceResponse:
        """
        Refresh data for a specific source and invalidate cache.
        
        Args:
            source_id: Unique identifier for the data source
            
        Returns:
            DataSourceResponse with refresh status
        """
        try:
            service = self.get_service_for_source(source_id)
            if not service:
                return self._create_error_response(
                    'DATA_SOURCE_NOT_FOUND',
                    f'No service available for data source: {source_id}',
                    {'source_id': source_id}
                )

            # Invalidate cache for this source
            self._invalidate_cache_for_source(source_id)
            
            # Refresh data
            response = service.refresh_data(source_id)
            
            return response

        except Exception as e:
            self.logger.error(f"Error refreshing data for source {source_id}: {str(e)}")
            return self._create_error_response(
                'INTERNAL_ERROR',
                f'Internal error refreshing data: {str(e)}',
                {'source_id': source_id}
            )

    def get_status(self, source_id: str) -> DataSourceResponse:
        """
        Get connection and health status for a data source.
        
        Args:
            source_id: Unique identifier for the data source
            
        Returns:
            DataSourceResponse with status information
        """
        try:
            service = self.get_service_for_source(source_id)
            if not service:
                return self._create_error_response(
                    'DATA_SOURCE_NOT_FOUND',
                    f'No service available for data source: {source_id}',
                    {'source_id': source_id}
                )

            return service.get_status(source_id)

        except Exception as e:
            self.logger.error(f"Error getting status for source {source_id}: {str(e)}")
            return self._create_error_response(
                'INTERNAL_ERROR',
                f'Internal error retrieving status: {str(e)}',
                {'source_id': source_id}
            )

    def validate_source(self, source_config: Dict[str, Any]) -> DataSourceResponse:
        """
        Validate data source configuration.
        
        Args:
            source_config: Configuration parameters for the data source
            
        Returns:
            DataSourceResponse with validation results
        """
        try:
            source_type = source_config.get('type')
            if not source_type:
                return self._create_error_response(
                    'INVALID_CONFIG',
                    'Data source type is required',
                    {'config': source_config}
                )

            # Find service by type
            service = None
            for svc in self._services.values():
                if hasattr(svc, 'service_type') and svc.service_type == source_type:
                    service = svc
                    break

            if not service:
                return self._create_error_response(
                    'UNSUPPORTED_TYPE',
                    f'No service available for data source type: {source_type}',
                    {'type': source_type}
                )

            return service.validate_source(source_config)

        except Exception as e:
            self.logger.error(f"Error validating source config: {str(e)}")
            return self._create_error_response(
                'INTERNAL_ERROR',
                f'Internal error validating source: {str(e)}',
                {'config': source_config}
            )

    def get_available_services(self) -> List[str]:
        """Get list of registered service names"""
        return list(self._services.keys())

    def _get_cache_client(self) -> Optional[redis.Redis]:
        """Get Redis cache client if available"""
        if self._cache is None:
            try:
                # Try to get cache manager from Flask app
                if current_app and hasattr(current_app, 'cache_manager'):
                    cache_manager = current_app.cache_manager
                    if cache_manager and cache_manager.redis_client:
                        self._cache = cache_manager.redis_client
                        self.logger.info("Connected to Redis cache via CacheManager")
                        return self._cache
                
                # Fallback to direct Redis connection
                if current_app:
                    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
                    self._cache = redis.from_url(redis_url, decode_responses=True)
                    # Test connection
                    self._cache.ping()
                    self.logger.info("Connected to Redis cache directly")
            except Exception as e:
                self.logger.warning(f"Redis cache not available: {str(e)}")
                self._cache = False  # Mark as unavailable
        
        return self._cache if self._cache is not False else None

    def _generate_cache_key(self, operation: str, source_id: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a cache key for the operation"""
        key_parts = ['nextgen_ds', operation, source_id]
        if params:
            # Sort params for consistent key generation
            param_str = json.dumps(params, sort_keys=True)
            key_parts.append(param_str)
        return ':'.join(key_parts)

    def _get_from_cache(self, cache_key: str) -> Optional[DataSourceResponse]:
        """Get response from cache with metrics tracking"""
        cache_client = self._get_cache_client()
        if not cache_client:
            self._cache_stats['misses'] += 1
            return None

        try:
            cached_data = cache_client.get(cache_key)
            if cached_data:
                # Handle both string and bytes data
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode('utf-8')
                
                data = json.loads(cached_data)
                
                # Check if cache entry has version info for smart invalidation
                cache_version = data.get('_cache_version')
                source_id = self._extract_source_id_from_key(cache_key)
                
                if cache_version and source_id:
                    current_version = self._source_versions.get(source_id)
                    if current_version and current_version != cache_version:
                        # Cache is stale, invalidate and return None
                        cache_client.delete(cache_key)
                        self._cache_stats['invalidations'] += 1
                        self._cache_stats['misses'] += 1
                        return None
                
                # Reconstruct DataSourceResponse
                response = DataSourceResponse(
                    success=data['success'],
                    data=data.get('data'),
                    error=data.get('error'),
                    metadata=data.get('metadata'),
                    timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
                )
                
                self._cache_stats['hits'] += 1
                return response
            else:
                self._cache_stats['misses'] += 1
                
        except Exception as e:
            self.logger.warning(f"Error reading from cache: {str(e)}")
            self._cache_stats['errors'] += 1
        
        return None

    def _set_cache(self, cache_key: str, response: DataSourceResponse, ttl: int = 300) -> None:
        """Set response in cache with version tracking"""
        cache_client = self._get_cache_client()
        if not cache_client:
            return

        try:
            source_id = self._extract_source_id_from_key(cache_key)
            current_version = self._source_versions.get(source_id, str(int(time.time())))
            
            # Convert response to JSON-serializable format
            data = {
                'success': response.success,
                'data': response.data,
                'error': response.error,
                'metadata': response.metadata,
                'timestamp': response.timestamp.isoformat() if response.timestamp else None,
                '_cache_version': current_version,
                '_cached_at': datetime.utcnow().isoformat()
            }
            
            # Use CacheManager if available for better serialization
            if current_app and hasattr(current_app, 'cache_manager'):
                cache_manager = current_app.cache_manager
                cache_manager.set(cache_key, data, ttl)
            else:
                cache_client.setex(cache_key, ttl, json.dumps(data))
            
            self._cache_stats['sets'] += 1
            
        except Exception as e:
            self.logger.warning(f"Error writing to cache: {str(e)}")
            self._cache_stats['errors'] += 1

    def _invalidate_cache_for_source(self, source_id: str) -> None:
        """Invalidate all cache entries for a specific source"""
        cache_client = self._get_cache_client()
        if not cache_client:
            return

        try:
            # Find all keys for this source
            pattern = f"nextgen_ds:*:{source_id}*"
            keys = cache_client.keys(pattern)
            if keys:
                cache_client.delete(*keys)
                self.logger.debug(f"Invalidated {len(keys)} cache entries for source {source_id}")
        except Exception as e:
            self.logger.warning(f"Error invalidating cache: {str(e)}")

    def _extract_source_id_from_key(self, cache_key: str) -> Optional[str]:
        """Extract source ID from cache key"""
        try:
            parts = cache_key.split(':')
            if len(parts) >= 3:
                return parts[2]  # nextgen_ds:operation:source_id
        except Exception:
            pass
        return None
    
    def warm_cache_for_source(self, source_id: str, operations: List[str] = None) -> Dict[str, bool]:
        """
        Warm cache for frequently accessed data sources
        
        Args:
            source_id: Source to warm cache for
            operations: List of operations to warm (default: ['data', 'fields'])
            
        Returns:
            Dict with operation results
        """
        if not self._cache_warming_enabled:
            return {}
        
        operations = operations or ['data', 'fields']
        results = {}
        
        self.logger.info(f"Starting cache warming for source: {source_id}")
        
        for operation in operations:
            try:
                if operation == 'data':
                    response = self.get_data(source_id)
                elif operation == 'fields':
                    response = self.get_fields(source_id)
                else:
                    continue
                
                results[operation] = response.success
                if response.success:
                    self._cache_stats['warming_operations'] += 1
                    
            except Exception as e:
                self.logger.warning(f"Cache warming failed for {source_id}:{operation}: {e}")
                results[operation] = False
        
        self.logger.info(f"Cache warming completed for {source_id}: {results}")
        return results
    
    def warm_cache_for_frequently_accessed_sources(self) -> Dict[str, Dict[str, bool]]:
        """Warm cache for all frequently accessed sources"""
        results = {}
        
        for source_id in self._warm_cache_sources:
            results[source_id] = self.warm_cache_for_source(source_id)
        
        return results
    
    def add_to_cache_warming(self, source_id: str):
        """Add a source to the cache warming list"""
        self._warm_cache_sources.add(source_id)
        self.logger.info(f"Added {source_id} to cache warming list")
    
    def remove_from_cache_warming(self, source_id: str):
        """Remove a source from the cache warming list"""
        self._warm_cache_sources.discard(source_id)
        self.logger.info(f"Removed {source_id} from cache warming list")
    
    def update_source_version(self, source_id: str, version: str = None):
        """
        Update source version for smart cache invalidation
        
        Args:
            source_id: Source identifier
            version: Version string (defaults to current timestamp)
        """
        if version is None:
            version = str(int(time.time()))
        
        old_version = self._source_versions.get(source_id)
        self._source_versions[source_id] = version
        
        if old_version and old_version != version:
            # Invalidate cache for this source
            self._invalidate_cache_for_source(source_id)
            self.logger.info(f"Updated version for {source_id}: {old_version} -> {version}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        stats = self._cache_stats.copy()
        
        # Calculate hit rate
        total_requests = stats['hits'] + stats['misses']
        stats['hit_rate'] = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Add cache warming info
        stats['warm_cache_sources'] = list(self._warm_cache_sources)
        stats['cache_warming_enabled'] = self._cache_warming_enabled
        
        # Add Redis info if available
        cache_client = self._get_cache_client()
        if cache_client:
            try:
                # Count data source related keys
                pattern = "nextgen_ds:*"
                keys = cache_client.keys(pattern)
                stats['cached_keys_count'] = len(keys)
            except Exception as e:
                self.logger.warning(f"Could not get cache key count: {e}")
                stats['cached_keys_count'] = 'unknown'
        
        return stats
    
    def clear_cache_stats(self):
        """Clear cache statistics"""
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0,
            'errors': 0,
            'warming_operations': 0
        }
    
    def enable_cache_warming(self, enabled: bool = True):
        """Enable or disable cache warming"""
        self._cache_warming_enabled = enabled
        self.logger.info(f"Cache warming {'enabled' if enabled else 'disabled'}")
    
    def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health information"""
        health = {
            'cache_available': False,
            'cache_responsive': False,
            'error': None
        }
        
        cache_client = self._get_cache_client()
        if cache_client:
            health['cache_available'] = True
            try:
                # Test cache responsiveness
                test_key = "nextgen_ds:health_check"
                cache_client.setex(test_key, 10, "test")
                result = cache_client.get(test_key)
                cache_client.delete(test_key)
                
                health['cache_responsive'] = (result == "test" or result == b"test")
                
            except Exception as e:
                health['error'] = str(e)
        
        return health

    def _create_error_response(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> DataSourceResponse:
        """Create a standardized error response"""
        error_data = {
            'code': error_code,
            'message': message,
            'service': 'DataSourceManager'
        }
        if details:
            error_data['details'] = details

        self.logger.error(f"DataSourceManager error: {error_code} - {message}")
        
        return DataSourceResponse(
            success=False,
            error=error_data
        )