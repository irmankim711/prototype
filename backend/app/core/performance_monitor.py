"""
Database Performance Monitoring Utilities
Provides decorators and utilities for monitoring database query performance.
"""

import time
import logging
from functools import wraps
from sqlalchemy import event
from sqlalchemy.engine import Engine
from .. import db

logger = logging.getLogger(__name__)

class QueryPerformanceMonitor:
    """Monitor and log database query performance."""
    
    def __init__(self):
        self.query_times = []
        self.slow_query_threshold = 1.0  # seconds
        self.moderate_query_threshold = 0.5  # seconds
        
    def setup_query_monitoring(self):
        """Setup SQLAlchemy event listeners for query monitoring."""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # Log slow queries
            if total > self.slow_query_threshold:
                logger.warning(f"SLOW QUERY ({total:.3f}s): {statement[:200]}...")
            elif total > self.moderate_query_threshold:
                logger.info(f"Query timing ({total:.3f}s): {statement[:100]}...")
            
            # Store query time for analysis
            self.query_times.append({
                'duration': total,
                'statement': statement[:200],
                'timestamp': time.time()
            })
            
            # Keep only recent queries (last 1000)
            if len(self.query_times) > 1000:
                self.query_times = self.query_times[-1000:]
    
    def get_performance_stats(self):
        """Get performance statistics for recent queries."""
        if not self.query_times:
            return {
                'total_queries': 0,
                'avg_duration': 0,
                'slow_queries': 0,
                'moderate_queries': 0
            }
        
        durations = [q['duration'] for q in self.query_times]
        slow_queries = len([d for d in durations if d > self.slow_query_threshold])
        moderate_queries = len([d for d in durations if d > self.moderate_query_threshold])
        
        return {
            'total_queries': len(self.query_times),
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'slow_queries': slow_queries,
            'moderate_queries': moderate_queries,
            'slow_query_percentage': (slow_queries / len(durations)) * 100
        }

# Global performance monitor instance
performance_monitor = QueryPerformanceMonitor()

def monitor_query_performance(func):
    """Decorator to monitor individual function query performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            
            if duration > performance_monitor.slow_query_threshold:
                logger.warning(f"SLOW FUNCTION: {func.__name__} took {duration:.3f}s")
            elif duration > performance_monitor.moderate_query_threshold:
                logger.info(f"Function timing: {func.__name__} took {duration:.3f}s")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    return wrapper

def log_query_timing(query_name):
    """Decorator factory for logging query timing with custom names."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            
            if duration > 0.1:  # Log queries taking more than 100ms
                logger.info(f"Query '{query_name}' took {duration:.3f}s")
            
            return result
        return wrapper
    return decorator

class DatabaseConnectionMonitor:
    """Monitor database connection pool health."""
    
    @staticmethod
    def get_connection_pool_status():
        """Get current connection pool status."""
        try:
            pool = db.engine.pool
            return {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
        except Exception as e:
            logger.error(f"Error getting connection pool status: {str(e)}")
            return None
    
    @staticmethod
    def log_connection_pool_status():
        """Log current connection pool status."""
        status = DatabaseConnectionMonitor.get_connection_pool_status()
        if status:
            logger.info(f"Connection Pool Status: {status}")

def setup_performance_monitoring():
    """Setup all performance monitoring components."""
    performance_monitor.setup_query_monitoring()
    logger.info("Database performance monitoring initialized")

# Context manager for timing database operations
class QueryTimer:
    """Context manager for timing database operations."""
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            logger.error(f"Operation '{self.operation_name}' failed after {duration:.3f}s")
        elif duration > 1.0:
            logger.warning(f"SLOW OPERATION: '{self.operation_name}' took {duration:.3f}s")
        elif duration > 0.5:
            logger.info(f"Operation '{self.operation_name}' took {duration:.3f}s")

# Usage example:
# with QueryTimer("bulk_form_update"):
#     # database operations here
#     pass