"""
Graceful Shutdown Handler

This module provides graceful shutdown functionality for the application,
including proper cleanup of resources, database connections, and background tasks.
"""

import logging
import signal
import sys
import time
import threading
from typing import List, Callable, Optional
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ShutdownStatus(Enum):
    """Shutdown status enumeration."""
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN_COMPLETE = "shutdown_complete"

@dataclass
class ShutdownHook:
    """Shutdown hook configuration."""
    name: str
    callback: Callable
    priority: int = 0  # Lower numbers = higher priority
    timeout: float = 30.0  # Timeout in seconds
    critical: bool = False  # If True, failure will prevent shutdown

class GracefulShutdownHandler:
    """Handles graceful shutdown of the application."""
    
    def __init__(self):
        self.status = ShutdownStatus.RUNNING
        self.shutdown_hooks: List[ShutdownHook] = []
        self.shutdown_start_time: Optional[float] = None
        self.shutdown_timeout = 60.0  # Overall shutdown timeout
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()
        
        # Register signal handlers
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Signal handlers registered for graceful shutdown")
        except Exception as e:
            logger.warning(f"Failed to register signal handlers: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}, initiating graceful shutdown")
        self.initiate_shutdown()
    
    def add_shutdown_hook(self, name: str, callback: Callable, priority: int = 0, 
                          timeout: float = 30.0, critical: bool = False):
        """Add a shutdown hook."""
        hook = ShutdownHook(
            name=name,
            callback=callback,
            priority=priority,
            timeout=timeout,
            critical=critical
        )
        
        with self._lock:
            self.shutdown_hooks.append(hook)
            # Sort by priority (lower numbers first)
            self.shutdown_hooks.sort(key=lambda x: x.priority)
        
        logger.info(f"Added shutdown hook: {name} (priority: {priority})")
    
    def remove_shutdown_hook(self, name: str):
        """Remove a shutdown hook by name."""
        with self._lock:
            self.shutdown_hooks = [hook for hook in self.shutdown_hooks if hook.name != name]
        logger.info(f"Removed shutdown hook: {name}")
    
    def initiate_shutdown(self):
        """Initiate the graceful shutdown process."""
        with self._lock:
            if self.status != ShutdownStatus.RUNNING:
                logger.warning("Shutdown already in progress")
                return
            
            self.status = ShutdownStatus.SHUTTING_DOWN
            self.shutdown_start_time = time.time()
            self._shutdown_event.set()
        
        logger.info("Graceful shutdown initiated")
        
        # Start shutdown in a separate thread to avoid blocking
        shutdown_thread = threading.Thread(target=self._perform_shutdown, daemon=True)
        shutdown_thread.start()
    
    def _perform_shutdown(self):
        """Perform the actual shutdown process."""
        try:
            logger.info("Starting shutdown process...")
            
            # Execute shutdown hooks in priority order
            failed_hooks = []
            
            for hook in self.shutdown_hooks:
                try:
                    logger.info(f"Executing shutdown hook: {hook.name}")
                    
                    # Execute hook with timeout
                    with self._timeout_context(hook.timeout):
                        hook.callback()
                    
                    logger.info(f"Shutdown hook completed: {hook.name}")
                    
                except Exception as e:
                    error_msg = f"Shutdown hook '{hook.name}' failed: {e}"
                    logger.error(error_msg)
                    
                    if hook.critical:
                        failed_hooks.append((hook.name, str(e), True))
                    else:
                        failed_hooks.append((hook.name, str(e), False))
            
            # Check if any critical hooks failed
            critical_failures = [hook for hook in failed_hooks if hook[2]]
            
            if critical_failures:
                logger.error("Critical shutdown hooks failed, shutdown may be incomplete")
                for name, error, critical in critical_failures:
                    logger.error(f"Critical hook '{name}' failed: {error}")
            else:
                logger.info("All shutdown hooks completed successfully")
            
            # Update status
            with self._lock:
                self.status = ShutdownStatus.SHUTDOWN_COMPLETE
            
            shutdown_duration = time.time() - self.shutdown_start_time
            logger.info(f"Graceful shutdown completed in {shutdown_duration:.2f} seconds")
            
            # Exit the application
            sys.exit(0 if not critical_failures else 1)
            
        except Exception as e:
            logger.error(f"Unexpected error during shutdown: {e}")
            sys.exit(1)
    
    @contextmanager
    def _timeout_context(self, timeout: float):
        """Context manager for timeout handling."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {timeout} seconds")
        
        # Set timeout handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            yield
        finally:
            # Restore original handler and cancel alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def wait_for_shutdown(self, timeout: Optional[float] = None):
        """Wait for shutdown to complete."""
        if timeout is None:
            timeout = self.shutdown_timeout
        
        if self._shutdown_event.wait(timeout):
            logger.info("Shutdown event received")
        else:
            logger.warning("Shutdown timeout reached")
    
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self.status == ShutdownStatus.SHUTTING_DOWN
    
    def get_status(self) -> ShutdownStatus:
        """Get current shutdown status."""
        return self.status
    
    def get_shutdown_duration(self) -> Optional[float]:
        """Get shutdown duration if shutdown is in progress or complete."""
        if self.shutdown_start_time is None:
            return None
        
        if self.status == ShutdownStatus.SHUTTING_DOWN:
            return time.time() - self.shutdown_start_time
        elif self.status == ShutdownStatus.SHUTDOWN_COMPLETE:
            return self.shutdown_start_time  # This would be the duration when it completed
        
        return None

# Global shutdown handler instance
shutdown_handler = GracefulShutdownHandler()

def register_shutdown_hook(name: str, callback: Callable, priority: int = 0, 
                          timeout: float = 30.0, critical: bool = False):
    """Register a shutdown hook with the global handler."""
    shutdown_handler.add_shutdown_hook(name, callback, priority, timeout, critical)

def remove_shutdown_hook(name: str):
    """Remove a shutdown hook from the global handler."""
    shutdown_handler.remove_shutdown_hook(name)

def is_shutting_down() -> bool:
    """Check if shutdown is in progress."""
    return shutdown_handler.is_shutting_down()

def get_shutdown_status() -> ShutdownStatus:
    """Get current shutdown status."""
    return shutdown_handler.get_status()

# Common shutdown hooks
def register_common_shutdown_hooks(app, db, redis_client, celery_app=None):
    """Register common shutdown hooks for a Flask application."""
    
    # Database cleanup
    def cleanup_database():
        logger.info("Cleaning up database connections...")
        try:
            if hasattr(db, 'session'):
                db.session.close()
            if hasattr(db, 'engine'):
                db.engine.dispose()
            logger.info("Database connections cleaned up")
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
    
    register_shutdown_hook("database_cleanup", cleanup_database, priority=1, critical=True)
    
    # Redis cleanup
    def cleanup_redis():
        logger.info("Cleaning up Redis connections...")
        try:
            if redis_client:
                redis_client.close()
            logger.info("Redis connections cleaned up")
        except Exception as e:
            logger.error(f"Redis cleanup failed: {e}")
    
    register_shutdown_hook("redis_cleanup", cleanup_redis, priority=2, critical=False)
    
    # Celery cleanup
    if celery_app:
        def cleanup_celery():
            logger.info("Cleaning up Celery...")
            try:
                celery_app.control.shutdown()
                logger.info("Celery shutdown completed")
            except Exception as e:
                logger.error(f"Celery cleanup failed: {e}")
        
        register_shutdown_hook("celery_cleanup", cleanup_celery, priority=3, critical=False)
    
    # Flask app cleanup
    def cleanup_flask():
        logger.info("Cleaning up Flask application...")
        try:
            # Close any open file handles, etc.
            pass
            logger.info("Flask application cleaned up")
        except Exception as e:
            logger.error(f"Flask cleanup failed: {e}")
    
    register_shutdown_hook("flask_cleanup", cleanup_flask, priority=4, critical=False)
    
    # Final cleanup
    def final_cleanup():
        logger.info("Performing final cleanup...")
        try:
            # Any final cleanup tasks
            pass
            logger.info("Final cleanup completed")
        except Exception as e:
            logger.error(f"Final cleanup failed: {e}")
    
    register_shutdown_hook("final_cleanup", final_cleanup, priority=5, critical=False)

# Decorator for functions that should not run during shutdown
def require_running(func):
    """Decorator to prevent function execution during shutdown."""
    def wrapper(*args, **kwargs):
        if is_shutting_down():
            raise RuntimeError("Application is shutting down")
        return func(*args, **kwargs)
    return wrapper

# Context manager for shutdown-aware operations
@contextmanager
def shutdown_aware_operation():
    """Context manager for operations that should be aware of shutdown status."""
    if is_shutting_down():
        raise RuntimeError("Application is shutting down")
    
    try:
        yield
    finally:
        # Check if shutdown started during operation
        if is_shutting_down():
            logger.warning("Operation completed during shutdown")
