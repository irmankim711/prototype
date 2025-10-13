"""
Application Performance Monitoring

This module provides:
- Performance monitoring hooks
- Metrics collection
- Structured logging with correlation IDs
- Prometheus metrics integration
"""

import logging
import time
import uuid
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
from collections import defaultdict, deque
import json

from flask import request, g, current_app
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration in seconds', ['method', 'endpoint'])
REQUEST_SIZE = Histogram('http_request_size_bytes', 'HTTP request size in bytes', ['method', 'endpoint'])
RESPONSE_SIZE = Histogram('http_response_size_bytes', 'HTTP response size in bytes', ['method', 'endpoint'])

ACTIVE_REQUESTS = Gauge('http_active_requests', 'Number of active HTTP requests', ['method', 'endpoint'])
ERROR_COUNT = Counter('http_errors_total', 'Total HTTP errors', ['method', 'endpoint', 'error_type'])

# Database metrics
DB_QUERY_COUNT = Counter('database_queries_total', 'Total database queries', ['operation', 'table'])
DB_QUERY_DURATION = Histogram('database_query_duration_seconds', 'Database query duration in seconds', ['operation', 'table'])
DB_CONNECTION_COUNT = Gauge('database_connections_active', 'Number of active database connections')

# Redis metrics
REDIS_OPERATION_COUNT = Counter('redis_operations_total', 'Total Redis operations', ['operation'])
REDIS_OPERATION_DURATION = Histogram('redis_operation_duration_seconds', 'Redis operation duration in seconds', ['operation'])
REDIS_CONNECTION_COUNT = Gauge('redis_connections_active', 'Number of active Redis connections')

# Business metrics
USER_LOGIN_COUNT = Counter('user_logins_total', 'Total user logins', ['status'])
FORM_SUBMISSION_COUNT = Counter('form_submissions_total', 'Total form submissions', ['status'])
REPORT_GENERATION_COUNT = Counter('report_generations_total', 'Total report generations', ['status'])

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    request_id: str
    endpoint: str
    method: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    database_queries: int = 0
    redis_operations: int = 0
    external_api_calls: int = 0
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

class CorrelationIDMiddleware:
    """Middleware for adding correlation IDs to requests."""
    
    def __init__(self, app):
        self.app = app
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
    
    def _before_request(self):
        """Set correlation ID before each request."""
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        
        # Store in Flask g for request context
        g.correlation_id = correlation_id
        g.request_start_time = time.time()
        
        # Add to request context for logging
        g.request_id = str(uuid.uuid4())
        g.user_id = getattr(g, 'jwt_identity', None)
        g.ip_address = request.remote_addr
        g.user_agent = request.headers.get('User-Agent')
        
        # Log request start
        logger.info("Request started", extra={
            'correlation_id': correlation_id,
            'request_id': g.request_id,
            'method': request.method,
            'endpoint': request.endpoint,
            'ip_address': g.ip_address,
            'user_agent': g.user_agent,
            'user_id': g.user_id,
        })
    
    def _after_request(self, response):
        """Log request completion and add correlation ID to response."""
        # Add correlation ID to response headers
        if hasattr(g, 'correlation_id'):
            response.headers['X-Correlation-ID'] = g.correlation_id
        
        # Calculate request duration
        duration = (time.time() - g.request_start_time) * 1000
        
        # Log request completion
        logger.info("Request completed", extra={
            'correlation_id': g.correlation_id,
            'request_id': g.request_id,
            'method': request.method,
            'endpoint': request.endpoint,
            'status_code': response.status_code,
            'duration_ms': round(duration, 2),
            'response_size': len(response.get_data()),
            'user_id': g.user_id,
        })
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint, status=response.status_code).inc()
        REQUEST_DURATION.labels(method=request.method, endpoint=request.endpoint).observe(duration / 1000)
        RESPONSE_SIZE.labels(method=request.method, endpoint=request.endpoint).observe(len(response.get_data()))
        
        return response

class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.active_requests = defaultdict(int)
        self.performance_data = deque(maxlen=1000)  # Keep last 1000 requests
        self.lock = threading.Lock()
    
    @contextmanager
    def monitor_request(self, endpoint: str, method: str, request_id: str):
        """Context manager for monitoring request performance."""
        metrics = PerformanceMetrics(
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            start_time=datetime.utcnow()
        )
        
        # Track active request
        with self.lock:
            self.active_requests[f"{method}:{endpoint}"] += 1
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
        
        try:
            yield metrics
        finally:
            # Complete metrics
            metrics.end_time = datetime.utcnow()
            metrics.duration_ms = (metrics.end_time - metrics.start_time).total_seconds() * 1000
            
            # Store metrics
            with self.lock:
                self.metrics[request_id] = metrics
                self.performance_data.append(metrics)
                
                # Update active request count
                self.active_requests[f"{method}:{endpoint}"] -= 1
                ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()
    
    def record_database_query(self, operation: str, table: str, duration_ms: float):
        """Record database query metrics."""
        DB_QUERY_COUNT.labels(operation=operation, table=table).inc()
        DB_QUERY_DURATION.labels(operation=operation, table=table).observe(duration_ms / 1000)
        
        # Update current request metrics if available
        if hasattr(g, 'request_id') and g.request_id in self.metrics:
            self.metrics[g.request_id].database_queries += 1
    
    def record_redis_operation(self, operation: str, duration_ms: float):
        """Record Redis operation metrics."""
        REDIS_OPERATION_COUNT.labels(operation=operation).inc()
        REDIS_OPERATION_DURATION.labels(operation=operation).observe(duration_ms / 1000)
        
        # Update current request metrics if available
        if hasattr(g, 'request_id') and g.request_id in self.metrics:
            self.metrics[g.request_id].redis_operations += 1
    
    def record_external_api_call(self, api_name: str, duration_ms: float, status_code: int):
        """Record external API call metrics."""
        # Update current request metrics if available
        if hasattr(g, 'request_id') and g.request_id in self.metrics:
            self.metrics[g.request_id].external_api_calls += 1
    
    def record_business_metric(self, metric_name: str, labels: Dict[str, str], value: float = 1):
        """Record business metrics."""
        if metric_name == 'user_logins':
            USER_LOGIN_COUNT.labels(**labels).inc()
        elif metric_name == 'form_submissions':
            FORM_SUBMISSION_COUNT.labels(**labels).inc()
        elif metric_name == 'report_generations':
            REPORT_GENERATION_COUNT.labels(**labels).inc()
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [
                m for m in self.performance_data 
                if m.start_time > cutoff_time
            ]
        
        if not recent_metrics:
            return {"message": "No metrics available for the specified time period"}
        
        # Calculate statistics
        durations = [m.duration_ms for m in recent_metrics if m.duration_ms]
        status_codes = [m.status_code for m in recent_metrics if m.status_code]
        
        summary = {
            "time_period_hours": hours,
            "total_requests": len(recent_metrics),
            "unique_endpoints": len(set(m.endpoint for m in recent_metrics)),
            "average_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "min_duration_ms": round(min(durations), 2) if durations else 0,
            "max_duration_ms": round(max(durations), 2) if durations else 0,
            "total_database_queries": sum(m.database_queries for m in recent_metrics),
            "total_redis_operations": sum(m.redis_operations for m in recent_metrics),
            "total_external_api_calls": sum(m.external_api_calls for m in recent_metrics),
            "status_code_distribution": defaultdict(int),
            "endpoint_distribution": defaultdict(int),
            "active_requests": dict(self.active_requests),
        }
        
        # Status code distribution
        for status in status_codes:
            summary["status_code_distribution"][str(status)] += 1
        
        # Endpoint distribution
        for metric in recent_metrics:
            summary["endpoint_distribution"][metric.endpoint] += 1
        
        return summary
    
    def get_metrics_for_request(self, request_id: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a specific request."""
        return self.metrics.get(request_id)

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(endpoint: str = None, method: str = None):
    """Decorator for monitoring function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get endpoint and method from function if not provided
            nonlocal endpoint, method
            if not endpoint:
                endpoint = func.__name__
            if not method:
                method = "FUNCTION"
            
            request_id = str(uuid.uuid4())
            
            with performance_monitor.monitor_request(endpoint, method, request_id):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Record error
                    if hasattr(g, 'request_id') and g.request_id in performance_monitor.metrics:
                        performance_monitor.metrics[g.request_id].error = str(e)
                    raise
        return wrapper
    return decorator

def monitor_database_queries(operation: str, table: str):
    """Decorator for monitoring database query performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                performance_monitor.record_database_query(operation, table, duration_ms)
        return wrapper
    return decorator

def monitor_redis_operations(operation: str):
    """Decorator for monitoring Redis operation performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                performance_monitor.record_redis_operation(operation, duration_ms)
        return wrapper
    return decorator

class StructuredLogger:
    """Structured logging with correlation IDs and context."""
    
    def __init__(self, logger_instance: logging.Logger):
        self.logger = logger_instance
    
    def log(self, level: str, message: str, **kwargs):
        """Log with structured data."""
        # Add correlation context if available
        context = {}
        if hasattr(g, 'correlation_id'):
            context['correlation_id'] = g.correlation_id
        if hasattr(g, 'request_id'):
            context['request_id'] = g.request_id
        if hasattr(g, 'user_id'):
            context['user_id'] = g.user_id
        if hasattr(g, 'ip_address'):
            context['ip_address'] = g.ip_address
        
        # Merge with provided kwargs
        log_data = {**context, **kwargs}
        
        # Format as JSON for structured logging
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.upper(),
            'message': message,
            **log_data
        }
        
        # Log using appropriate level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        """Log info level message."""
        self.log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message."""
        self.log('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level message."""
        self.log('error', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message."""
        self.log('debug', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical level message."""
        self.log('critical', message, **kwargs)

# Global structured logger instance
structured_logger = StructuredLogger(logger)

def get_metrics():
    """Get Prometheus metrics."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
