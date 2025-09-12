"""
Error Handling Configuration

This module provides configuration settings for the error handling system,
including Sentry configuration, logging settings, and error response options.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SentryConfig:
    """Configuration for Sentry error tracking."""
    
    dsn: Optional[str] = None
    environment: str = "development"
    traces_sample_rate: float = 0.1
    profiles_sample_rate: float = 0.1
    debug: bool = False
    before_send: Optional[callable] = None
    
    @classmethod
    def from_env(cls) -> 'SentryConfig':
        """Create SentryConfig from environment variables."""
        return cls(
            dsn=os.getenv('SENTRY_DSN'),
            environment=os.getenv('FLASK_ENV', 'development'),
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
            debug=os.getenv('SENTRY_DEBUG', 'false').lower() == 'true'
        )


@dataclass
class LoggingConfig:
    """Configuration for error logging."""
    
    level: str = "INFO"
    format: str = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    file_path: str = "logs/app.log"
    max_bytes: int = 10240000
    backup_count: int = 10
    include_stack_trace: bool = True
    include_request_details: bool = True
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create LoggingConfig from environment variables."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format=os.getenv('LOG_FORMAT', cls.format),
            file_path=os.getenv('LOG_FILE_PATH', cls.file_path),
            max_bytes=int(os.getenv('LOG_MAX_BYTES', str(cls.max_bytes))),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', str(cls.backup_count))),
            include_stack_trace=os.getenv('LOG_INCLUDE_STACK_TRACE', 'true').lower() == 'true',
            include_request_details=os.getenv('LOG_INCLUDE_REQUEST_DETAILS', 'true').lower() == 'true'
        )


@dataclass
class ErrorResponseConfig:
    """Configuration for error response formatting."""
    
    include_details_in_production: bool = False
    include_stack_trace: bool = False
    include_request_id: bool = True
    include_timestamp: bool = True
    include_error_code: bool = True
    include_field_errors: bool = True
    
    @classmethod
    def from_env(cls) -> 'ErrorResponseConfig':
        """Create ErrorResponseConfig from environment variables."""
        return cls(
            include_details_in_production=os.getenv('ERROR_INCLUDE_DETAILS_IN_PRODUCTION', 'false').lower() == 'true',
            include_stack_trace=os.getenv('ERROR_INCLUDE_STACK_TRACE', 'false').lower() == 'true',
            include_request_id=os.getenv('ERROR_INCLUDE_REQUEST_ID', 'true').lower() == 'true',
            include_timestamp=os.getenv('ERROR_INCLUDE_TIMESTAMP', 'true').lower() == 'true',
            include_error_code=os.getenv('ERROR_INCLUDE_ERROR_CODE', 'true').lower() == 'true',
            include_field_errors=os.getenv('ERROR_INCLUDE_FIELD_ERRORS', 'true').lower() == 'true'
        )


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting error handling."""
    
    retry_after_header: bool = True
    include_limit_info: bool = True
    default_retry_after: int = 60
    
    @classmethod
    def from_env(cls) -> 'RateLimitConfig':
        """Create RateLimitConfig from environment variables."""
        return cls(
            retry_after_header=os.getenv('RATE_LIMIT_RETRY_AFTER_HEADER', 'true').lower() == 'true',
            include_limit_info=os.getenv('RATE_LIMIT_INCLUDE_INFO', 'true').lower() == 'true',
            default_retry_after=int(os.getenv('RATE_LIMIT_DEFAULT_RETRY_AFTER', str(cls.default_retry_after)))
        )


@dataclass
class DatabaseErrorConfig:
    """Configuration for database error handling."""
    
    include_sql_details: bool = False
    include_table_info: bool = True
    include_constraint_info: bool = True
    user_friendly_messages: bool = True
    
    @classmethod
    def from_env(cls) -> 'DatabaseErrorConfig':
        """Create DatabaseErrorConfig from environment variables."""
        return cls(
            include_sql_details=os.getenv('DB_ERROR_INCLUDE_SQL_DETAILS', 'false').lower() == 'true',
            include_table_info=os.getenv('DB_ERROR_INCLUDE_TABLE_INFO', 'true').lower() == 'true',
            include_constraint_info=os.getenv('DB_ERROR_INCLUDE_CONSTRAINT_INFO', 'true').lower() == 'true',
            user_friendly_messages=os.getenv('DB_ERROR_USER_FRIENDLY_MESSAGES', 'true').lower() == 'true'
        )


@dataclass
class ValidationErrorConfig:
    """Configuration for validation error handling."""
    
    include_field_paths: bool = True
    include_validation_rules: bool = False
    include_suggestions: bool = True
    max_field_errors: int = 10
    
    @classmethod
    def from_env(cls) -> 'ValidationErrorConfig':
        """Create ValidationErrorConfig from environment variables."""
        return cls(
            include_field_paths=os.getenv('VALIDATION_INCLUDE_FIELD_PATHS', 'true').lower() == 'true',
            include_validation_rules=os.getenv('VALIDATION_INCLUDE_RULES', 'false').lower() == 'true',
            include_suggestions=os.getenv('VALIDATION_INCLUDE_SUGGESTIONS', 'true').lower() == 'true',
            max_field_errors=int(os.getenv('VALIDATION_MAX_FIELD_ERRORS', str(cls.max_field_errors)))
        )


@dataclass
class ErrorHandlingConfig:
    """Main configuration for the error handling system."""
    
    sentry: SentryConfig
    logging: LoggingConfig
    error_response: ErrorResponseConfig
    rate_limit: RateLimitConfig
    database: DatabaseErrorConfig
    validation: ValidationErrorConfig
    
    @classmethod
    def from_env(cls) -> 'ErrorHandlingConfig':
        """Create ErrorHandlingConfig from environment variables."""
        return cls(
            sentry=SentryConfig.from_env(),
            logging=LoggingConfig.from_env(),
            error_response=ErrorResponseConfig.from_env(),
            rate_limit=RateLimitConfig.from_env(),
            database=DatabaseErrorConfig.from_env(),
            validation=ValidationErrorConfig.from_env()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'sentry': {
                'dsn': self.sentry.dsn,
                'environment': self.sentry.environment,
                'traces_sample_rate': self.sentry.traces_sample_rate,
                'profiles_sample_rate': self.sentry.profiles_sample_rate,
                'debug': self.sentry.debug
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_bytes': self.logging.max_bytes,
                'backup_count': self.logging.backup_count,
                'include_stack_trace': self.logging.include_stack_trace,
                'include_request_details': self.logging.include_request_details
            },
            'error_response': {
                'include_details_in_production': self.error_response.include_details_in_production,
                'include_stack_trace': self.error_response.include_stack_trace,
                'include_request_id': self.error_response.include_request_id,
                'include_timestamp': self.error_response.include_timestamp,
                'include_error_code': self.error_response.include_error_code,
                'include_field_errors': self.error_response.include_field_errors
            },
            'rate_limit': {
                'retry_after_header': self.rate_limit.retry_after_header,
                'include_limit_info': self.rate_limit.include_limit_info,
                'default_retry_after': self.rate_limit.default_retry_after
            },
            'database': {
                'include_sql_details': self.database.include_sql_details,
                'include_table_info': self.database.include_table_info,
                'include_constraint_info': self.database.include_constraint_info,
                'user_friendly_messages': self.database.user_friendly_messages
            },
            'validation': {
                'include_field_paths': self.validation.include_field_paths,
                'include_validation_rules': self.validation.include_validation_rules,
                'include_suggestions': self.validation.include_suggestions,
                'max_field_errors': self.validation.max_field_errors
            }
        }


# Default configuration
DEFAULT_CONFIG = ErrorHandlingConfig(
    sentry=SentryConfig(),
    logging=LoggingConfig(),
    error_response=ErrorResponseConfig(),
    rate_limit=RateLimitConfig(),
    database=DatabaseErrorConfig(),
    validation=ValidationErrorConfig()
)


def get_error_config() -> ErrorHandlingConfig:
    """Get error handling configuration."""
    return ErrorHandlingConfig.from_env()


def get_sentry_config() -> SentryConfig:
    """Get Sentry configuration."""
    return SentryConfig.from_env()


def get_logging_config() -> LoggingConfig:
    """Get logging configuration."""
    return LoggingConfig.from_env()


def get_error_response_config() -> ErrorResponseConfig:
    """Get error response configuration."""
    return ErrorResponseConfig.from_env()
