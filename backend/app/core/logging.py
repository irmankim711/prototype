"""
Production-Grade Logging System
Structured logging with performance monitoring, security auditing, and observability
"""

import os
import sys
import json
import logging
import logging.config
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
from pathlib import Path
import traceback
from functools import wraps
import time
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log category enumeration"""
    SYSTEM = "system"
    SECURITY = "security"
    API = "api"
    DATABASE = "database"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    AUDIT = "audit"

@dataclass
class LogContext:
    """Structured log context"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging
    """
    
    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add thread and process info if available
        if hasattr(record, 'thread') and record.thread:
            log_entry["thread_id"] = record.thread
        if hasattr(record, 'process') and record.process:
            log_entry["process_id"] = record.process
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add custom attributes
        for attr in ['category', 'context', 'duration', 'status_code', 'extra_data']:
            if hasattr(record, attr):
                value = getattr(record, attr)
                if attr == 'duration':
                    log_entry["duration_ms"] = value
                elif attr == 'extra_data':
                    log_entry["extra"] = value
                else:
                    log_entry[attr] = value
        
        return json.dumps(log_entry, ensure_ascii=False)

class PerformanceLogger:
    """
    Performance monitoring and logging
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = {
            'total_requests': 0,
            'slow_requests': 0,
            'error_requests': 0,
            'avg_response_time': 0.0
        }
        self.response_times = []
    
    def log_request(
        self,
        method: str,
        endpoint: str,
        duration: float,
        status_code: int,
        context: Optional[LogContext] = None
    ):
        """Log API request with performance metrics"""
        
        self.metrics['total_requests'] += 1
        self.response_times.append(duration)
        
        # Keep only last 1000 response times for rolling average
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        self.metrics['avg_response_time'] = sum(self.response_times) / len(self.response_times)
        
        # Check for slow requests (>1 second)
        is_slow = duration > 1000
        if is_slow:
            self.metrics['slow_requests'] += 1
        
        # Check for error responses
        is_error = status_code >= 400
        if is_error:
            self.metrics['error_requests'] += 1
        
        # Log with appropriate level
        level = logging.WARNING if is_slow else logging.INFO
        if is_error:
            level = logging.ERROR
        
        self.logger.log(
            level,
            f"{method} {endpoint} - {status_code} - {duration:.2f}ms",
            extra={
                'category': LogCategory.PERFORMANCE.value,
                'context': context.to_dict() if context else {},
                'duration': duration,
                'status_code': status_code,
                'is_slow': is_slow,
                'is_error': is_error,
                'extra_data': {
                    'method': method,
                    'endpoint': endpoint,
                    'metrics': self.metrics
                }
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.metrics,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

class SecurityLogger:
    """
    Security event logging and auditing
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.security_events = {
            'login_attempts': 0,
            'failed_logins': 0,
            'token_validations': 0,
            'failed_validations': 0,
            'suspicious_activities': 0
        }
    
    def log_login_attempt(
        self,
        user_id: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log login attempt"""
        
        self.security_events['login_attempts'] += 1
        if not success:
            self.security_events['failed_logins'] += 1
        
        level = logging.INFO if success else logging.WARNING
        message = f"Login {'successful' if success else 'failed'} for user {user_id}"
        
        self.logger.log(
            level,
            message,
            extra={
                'category': LogCategory.SECURITY.value,
                'context': {
                    'user_id': user_id,
                    'ip_address': ip_address,
                    'user_agent': user_agent
                },
                'extra_data': {
                    'event_type': 'login_attempt',
                    'success': success,
                    'reason': reason,
                    'metrics': self.security_events
                }
            }
        )
    
    def log_token_validation(
        self,
        user_id: Optional[str],
        token_type: str,
        success: bool,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log token validation event"""
        
        self.security_events['token_validations'] += 1
        if not success:
            self.security_events['failed_validations'] += 1
        
        level = logging.DEBUG if success else logging.WARNING
        message = f"Token validation {'successful' if success else 'failed'} for user {user_id}"
        
        self.logger.log(
            level,
            message,
            extra={
                'category': LogCategory.SECURITY.value,
                'context': {
                    'user_id': user_id,
                    'ip_address': ip_address
                },
                'extra_data': {
                    'event_type': 'token_validation',
                    'token_type': token_type,
                    'success': success,
                    'reason': reason,
                    'metrics': self.security_events
                }
            }
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        severity: str = 'medium'
    ):
        """Log suspicious security activity"""
        
        self.security_events['suspicious_activities'] += 1
        
        # Map severity to log level
        level_map = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }
        level = level_map.get(severity, logging.WARNING)
        
        self.logger.log(
            level,
            f"Suspicious activity detected: {description}",
            extra={
                'category': LogCategory.SECURITY.value,
                'context': {
                    'user_id': user_id,
                    'ip_address': ip_address
                },
                'extra_data': {
                    'event_type': 'suspicious_activity',
                    'activity_type': activity_type,
                    'severity': severity,
                    'description': description,
                    'metrics': self.security_events
                }
            }
        )

class ApplicationLogger:
    """
    Main application logger with structured logging and monitoring
    """
    
    def __init__(
        self,
        name: str = "app",
        level: Union[str, int] = logging.INFO,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_json: bool = True
    ):
        """
        Initialize application logger
        
        Args:
            name: Logger name
            level: Log level
            log_file: Log file path (optional)
            enable_console: Enable console output
            enable_json: Enable JSON formatting
        """
        
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Performance and security loggers
        self.performance = PerformanceLogger(self.logger)
        self.security = SecurityLogger(self.logger)
        
        # Setup handlers
        self._setup_handlers(log_file, enable_console, enable_json)
        
        # Application metrics
        self.metrics = {
            'log_entries': 0,
            'errors': 0,
            'warnings': 0,
            'start_time': datetime.now(timezone.utc).isoformat()
        }
    
    def _setup_handlers(self, log_file: Optional[str], enable_console: bool, enable_json: bool):
        """Setup log handlers"""
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            if enable_json:
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log warning message"""
        self.metrics['warnings'] += 1
        self._log(logging.WARNING, message, context, **kwargs)
    
    def error(self, message: str, context: Optional[LogContext] = None, exc_info: bool = True, **kwargs):
        """Log error message"""
        self.metrics['errors'] += 1
        self._log(logging.ERROR, message, context, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, context: Optional[LogContext] = None, exc_info: bool = True, **kwargs):
        """Log critical message"""
        self.metrics['errors'] += 1
        self._log(logging.CRITICAL, message, context, exc_info=exc_info, **kwargs)
    
    def _log(
        self,
        level: int,
        message: str,
        context: Optional[LogContext] = None,
        category: Optional[LogCategory] = None,
        exc_info: bool = False,
        **kwargs
    ):
        """Internal log method"""
        
        self.metrics['log_entries'] += 1
        
        extra = {
            'category': category.value if category else LogCategory.SYSTEM.value,
            'context': context.to_dict() if context else {},
            'extra_data': kwargs
        }
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def audit(self, action: str, user_id: Optional[str] = None, resource: Optional[str] = None, **kwargs):
        """Log audit event"""
        
        context = LogContext(user_id=user_id)
        message = f"Audit: {action}"
        if resource:
            message += f" on {resource}"
        
        self._log(
            logging.INFO,
            message,
            context=context,
            category=LogCategory.AUDIT,
            action=action,
            resource=resource,
            **kwargs
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get combined logger metrics"""
        return {
            'logger': self.metrics,
            'performance': self.performance.get_metrics(),
            'security': self.security.security_events,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def performance_monitor(logger: Optional[ApplicationLogger] = None):
    """
    Decorator for monitoring function performance
    
    Args:
        logger: Logger instance (uses default if None)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                if logger:
                    logger.debug(
                        f"Function {func.__name__} completed in {duration:.2f}ms",
                        category=LogCategory.PERFORMANCE,
                        duration=duration,
                        function=func.__name__,
                        success=True
                    )
                
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                if logger:
                    logger.error(
                        f"Function {func.__name__} failed after {duration:.2f}ms: {str(e)}",
                        category=LogCategory.PERFORMANCE,
                        duration=duration,
                        function=func.__name__,
                        success=False,
                        error=str(e)
                    )
                
                raise
        
        return wrapper
    return decorator

# Global logger instance
_app_logger = None

def get_logger(name: str = "app") -> ApplicationLogger:
    """
    Get application logger instance
    
    Args:
        name: Logger name
        
    Returns:
        ApplicationLogger instance
    """
    global _app_logger
    if _app_logger is None:
        # Configure based on environment
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_file = os.getenv('LOG_FILE')
        enable_json = os.getenv('LOG_JSON', 'true').lower() == 'true'
        
        _app_logger = ApplicationLogger(
            name=name,
            level=getattr(logging, log_level, logging.INFO),
            log_file=log_file,
            enable_json=enable_json
        )
    
    return _app_logger

def setup_logging():
    """Setup application logging configuration"""
    
    # Disable Flask's default logger in production
    if os.getenv('FLASK_ENV') == 'production':
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    
    # Get and configure main logger
    logger = get_logger()
    
    # Log startup message
    logger.info(
        "Application logging initialized",
        category=LogCategory.SYSTEM,
        environment=os.getenv('FLASK_ENV', 'development'),
        log_level=os.getenv('LOG_LEVEL', 'INFO')
    )
    
    return logger

# Convenience functions
def log_api_request(method: str, endpoint: str, duration: float, status_code: int, context: Optional[LogContext] = None):
    """Log API request using global logger"""
    logger = get_logger()
    logger.performance.log_request(method, endpoint, duration, status_code, context)

def log_security_event(event_type: str, **kwargs):
    """Log security event using global logger"""
    logger = get_logger()
    if event_type == 'login':
        logger.security.log_login_attempt(**kwargs)
    elif event_type == 'token_validation':
        logger.security.log_token_validation(**kwargs)
    elif event_type == 'suspicious_activity':
        logger.security.log_suspicious_activity(**kwargs)

def log_audit(action: str, **kwargs):
    """Log audit event using global logger"""
    logger = get_logger()
    logger.audit(action, **kwargs)
