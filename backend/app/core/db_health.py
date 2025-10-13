"""
Database Connection Health Monitoring and Management
Provides utilities for monitoring database connection health and implementing retry logic.
"""

import time
import logging
from functools import wraps
from sqlalchemy.exc import DisconnectionError, OperationalError, TimeoutError
from sqlalchemy import text
from .. import db

logger = logging.getLogger(__name__)

class DatabaseHealthMonitor:
    """Monitor and manage database connection health."""
    
    def __init__(self):
        self.connection_failures = 0
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
        self.max_retry_attempts = 3
        self.retry_delay = 1  # seconds
        
    def check_database_health(self):
        """Check database connection health."""
        try:
            with db.engine.connect() as connection:
                # Simple query to test connection
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                
            self.connection_failures = 0
            self.last_health_check = time.time()
            return True
            
        except Exception as e:
            self.connection_failures += 1
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def get_connection_pool_metrics(self):
        """Get detailed connection pool metrics."""
        try:
            pool = db.engine.pool
            
            metrics = {
                'pool_size': pool.size(),
                'checked_in_connections': pool.checkedin(),
                'checked_out_connections': pool.checkedout(),
                'overflow_connections': pool.overflow(),
                'invalid_connections': pool.invalid(),
                'total_connections': pool.checkedin() + pool.checkedout(),
                'connection_failures': self.connection_failures,
                'last_health_check': self.last_health_check,
                'pool_utilization': (pool.checkedout() / (pool.size() + pool.overflow())) * 100 if (pool.size() + pool.overflow()) > 0 else 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting connection pool metrics: {str(e)}")
            return None
    
    def log_pool_status(self):
        """Log current connection pool status."""
        metrics = self.get_connection_pool_metrics()
        if metrics:
            logger.info(f"DB Pool Status - Size: {metrics['pool_size']}, "
                       f"In Use: {metrics['checked_out_connections']}, "
                       f"Available: {metrics['checked_in_connections']}, "
                       f"Utilization: {metrics['pool_utilization']:.1f}%")
    
    def should_perform_health_check(self):
        """Check if it's time to perform a health check."""
        return (time.time() - self.last_health_check) > self.health_check_interval

# Global health monitor instance
db_health_monitor = DatabaseHealthMonitor()

def with_db_retry(max_retries=3, delay=1, backoff=2):
    """
    Decorator to retry database operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier for delay
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except (DisconnectionError, OperationalError, TimeoutError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Database operation {func.__name__} failed after {max_retries} retries: {str(e)}")
                        raise
                    
                    logger.warning(f"Database operation {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                                 f"retrying in {current_delay}s: {str(e)}")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
                    # Try to recover connection
                    try:
                        db.session.rollback()
                    except:
                        pass
                        
                except Exception as e:
                    # Non-connection related errors should not be retried
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise
            
            # This should never be reached, but just in case
            raise last_exception
            
        return wrapper
    return decorator

def check_connection_before_request():
    """Check database connection health before processing requests."""
    if db_health_monitor.should_perform_health_check():
        if not db_health_monitor.check_database_health():
            logger.warning("Database health check failed, connection may be unstable")

def cleanup_database_connections():
    """Clean up database connections and reset pool if needed."""
    try:
        # Close all connections in the pool
        db.engine.dispose()
        logger.info("Database connection pool disposed and reset")
        
    except Exception as e:
        logger.error(f"Error cleaning up database connections: {str(e)}")

class DatabaseConnectionContext:
    """Context manager for database operations with automatic retry and cleanup."""
    
    def __init__(self, operation_name, max_retries=3):
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        
        # Check connection health if needed
        if db_health_monitor.should_perform_health_check():
            db_health_monitor.check_database_health()
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            if isinstance(exc_val, (DisconnectionError, OperationalError, TimeoutError)):
                logger.error(f"Database connection error in {self.operation_name} after {duration:.3f}s: {str(exc_val)}")
                db_health_monitor.connection_failures += 1
            else:
                logger.error(f"Operation {self.operation_name} failed after {duration:.3f}s: {str(exc_val)}")
        else:
            if duration > 1.0:
                logger.warning(f"Slow database operation: {self.operation_name} took {duration:.3f}s")

def optimize_connection_pool():
    """Optimize connection pool settings based on current usage."""
    try:
        metrics = db_health_monitor.get_connection_pool_metrics()
        if not metrics:
            return
        
        utilization = metrics['pool_utilization']
        
        # Log recommendations based on utilization
        if utilization > 90:
            logger.warning(f"High connection pool utilization ({utilization:.1f}%). "
                          "Consider increasing pool_size or max_overflow.")
        elif utilization > 75:
            logger.info(f"Moderate connection pool utilization ({utilization:.1f}%). "
                       "Monitor for potential scaling needs.")
        
        # Log if there are invalid connections
        if metrics['invalid_connections'] > 0:
            logger.warning(f"Found {metrics['invalid_connections']} invalid connections. "
                          "Pool cleanup may be needed.")
            
    except Exception as e:
        logger.error(f"Error optimizing connection pool: {str(e)}")

# Usage examples:
# 
# @with_db_retry(max_retries=3, delay=1)
# def my_database_operation():
#     # database operations here
#     pass
#
# with DatabaseConnectionContext("bulk_update_operation"):
#     # database operations here
#     pass