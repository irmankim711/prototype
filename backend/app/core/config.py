"""
Enhanced Configuration Management System
Production-ready settings with environment validation and type safety
"""

import os
import logging
from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
from pathlib import Path
import redis
from functools import lru_cache

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///app.db'))
    pool_size: int = field(default_factory=lambda: int(os.getenv('DB_POOL_SIZE', '10')))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv('DB_POOL_TIMEOUT', '20')))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv('DB_POOL_RECYCLE', '3600')))
    max_overflow: int = field(default_factory=lambda: int(os.getenv('DB_MAX_OVERFLOW', '20')))
    echo: bool = field(default_factory=lambda: os.getenv('DB_ECHO', 'false').lower() == 'true')

@dataclass
class RedisConfig:
    """Redis configuration settings"""
    url: str = field(default_factory=lambda: os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    max_connections: int = field(default_factory=lambda: int(os.getenv('REDIS_MAX_CONNECTIONS', '20')))
    retry_on_timeout: bool = field(default_factory=lambda: os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true')
    health_check_interval: int = field(default_factory=lambda: int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30')))

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    secret_key: str = field(default_factory=lambda: os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'))
    jwt_secret_key: str = field(default_factory=lambda: os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production'))
    jwt_access_token_expires: int = field(default_factory=lambda: int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600')))  # seconds
    jwt_refresh_token_expires: int = field(default_factory=lambda: int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000')))  # 30 days
    password_hash_rounds: int = field(default_factory=lambda: int(os.getenv('PASSWORD_HASH_ROUNDS', '12')))
    encryption_key: Optional[str] = field(default_factory=lambda: os.getenv('ENCRYPTION_KEY'))

@dataclass
class GoogleConfig:
    """Google API configuration settings"""
    client_id: str = field(default_factory=lambda: os.getenv('GOOGLE_CLIENT_ID', ''))
    client_secret: str = field(default_factory=lambda: os.getenv('GOOGLE_CLIENT_SECRET', ''))
    redirect_uri: str = field(default_factory=lambda: os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/auth/google/callback'))
    scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/forms'
    ])

@dataclass
class MicrosoftConfig:
    """Microsoft Graph API configuration settings"""
    client_id: str = field(default_factory=lambda: os.getenv('MICROSOFT_CLIENT_ID', ''))
    client_secret: str = field(default_factory=lambda: os.getenv('MICROSOFT_CLIENT_SECRET', ''))
    tenant_id: str = field(default_factory=lambda: os.getenv('MICROSOFT_TENANT_ID', ''))
    redirect_uri: str = field(default_factory=lambda: os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:3000/auth/microsoft/callback'))

@dataclass
class EmailConfig:
    """Email configuration settings"""
    smtp_host: str = field(default_factory=lambda: os.getenv('SMTP_HOST', 'smtp.gmail.com'))
    smtp_port: int = field(default_factory=lambda: int(os.getenv('SMTP_PORT', '587')))
    smtp_user: Optional[str] = field(default_factory=lambda: os.getenv('SMTP_USER'))
    smtp_password: Optional[str] = field(default_factory=lambda: os.getenv('SMTP_PASSWORD'))
    from_email: Optional[str] = field(default_factory=lambda: os.getenv('EMAIL_FROM'))
    use_tls: bool = field(default_factory=lambda: os.getenv('SMTP_USE_TLS', 'true').lower() == 'true')

@dataclass
class AIConfig:
    """AI service configuration settings"""
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv('OPENAI_API_KEY'))
    openai_model: str = field(default_factory=lambda: os.getenv('OPENAI_MODEL', 'gpt-4'))
    max_tokens: int = field(default_factory=lambda: int(os.getenv('OPENAI_MAX_TOKENS', '4000')))
    temperature: float = field(default_factory=lambda: float(os.getenv('OPENAI_TEMPERATURE', '0.7')))

@dataclass
class CeleryConfig:
    """Celery configuration settings"""
    broker_url: str = field(default_factory=lambda: os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
    result_backend: str = field(default_factory=lambda: os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'))
    task_serializer: str = field(default_factory=lambda: os.getenv('CELERY_TASK_SERIALIZER', 'json'))
    result_serializer: str = field(default_factory=lambda: os.getenv('CELERY_RESULT_SERIALIZER', 'json'))
    accept_content: List[str] = field(default_factory=lambda: ['json'])
    timezone: str = field(default_factory=lambda: os.getenv('CELERY_TIMEZONE', 'UTC'))

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    default_limit: str = field(default_factory=lambda: os.getenv('RATELIMIT_DEFAULT', '200 per day; 50 per hour'))
    storage_url: str = field(default_factory=lambda: os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/0'))
    key_func: str = field(default_factory=lambda: 'lambda: request.remote_addr')

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    sentry_dsn: Optional[str] = field(default_factory=lambda: os.getenv('SENTRY_DSN'))
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    enable_metrics: bool = field(default_factory=lambda: os.getenv('ENABLE_METRICS', 'true').lower() == 'true')
    metrics_port: int = field(default_factory=lambda: int(os.getenv('METRICS_PORT', '8080')))

class Settings:
    """
    Comprehensive application settings with validation and environment support
    
    Features:
    - Environment-based configuration
    - Type safety with dataclasses
    - Validation and error handling
    - Caching for performance
    - Development/Production mode detection
    """
    
    def __init__(self):
        self.environment = os.getenv('FLASK_ENV', 'development')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.testing = os.getenv('TESTING', 'false').lower() == 'true'
        
        # Application metadata
        self.app_name = os.getenv('APP_NAME', 'Automated Report Platform')
        self.app_version = os.getenv('APP_VERSION', '1.0.0')
        self.app_host = os.getenv('APP_HOST', '0.0.0.0')
        self.app_port = int(os.getenv('APP_PORT', '5000'))
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.security = SecurityConfig()
        self.google = GoogleConfig()
        self.microsoft = MicrosoftConfig()
        self.email = EmailConfig()
        self.ai = AIConfig()
        self.celery = CeleryConfig()
        self.rate_limit = RateLimitConfig()
        self.monitoring = MonitoringConfig()
        
        # File upload settings
        self.max_content_length = int(os.getenv('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024)))  # 16MB
        self.upload_folder = Path(os.getenv('UPLOAD_FOLDER', 'uploads'))
        self.allowed_extensions = set(os.getenv('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg,gif,xlsx,csv').split(','))
        
        # CORS settings
        self.cors_origins = self._parse_list(os.getenv('CORS_ORIGINS', '*'))
        
        # Session settings
        self.session_cookie_secure = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
        self.session_cookie_httponly = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
        self.session_cookie_samesite = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
        
        # Validate critical settings
        self._validate_settings()
        
        # Setup logging
        self._setup_logging()
    
    def _parse_list(self, value: str, separator: str = ',') -> List[str]:
        """Parse comma-separated string into list"""
        if not value:
            return []
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    def _validate_settings(self) -> None:
        """Validate critical configuration settings"""
        errors = []
        
        # Check required environment variables for production
        if self.environment == 'production':
            required_vars = [
                ('SECRET_KEY', self.security.secret_key),
                ('JWT_SECRET_KEY', self.security.jwt_secret_key),
                ('DATABASE_URL', self.database.url),
            ]
            
            for var_name, var_value in required_vars:
                if not var_value or var_value.startswith('dev-') or var_value.startswith('jwt-'):
                    errors.append(f"Production environment requires {var_name} to be set")
        
        # Validate Google OAuth settings if enabled
        if self.google.client_id and not self.google.client_secret:
            errors.append("Google OAuth requires both CLIENT_ID and CLIENT_SECRET")
        
        # Validate Microsoft Graph settings if enabled
        if self.microsoft.client_id and (not self.microsoft.client_secret or not self.microsoft.tenant_id):
            errors.append("Microsoft Graph requires CLIENT_ID, CLIENT_SECRET, and TENANT_ID")
        
        # Validate database URL format
        if not self.database.url.startswith(('sqlite:///', 'postgresql://', 'mysql://')):
            errors.append("Invalid DATABASE_URL format")
        
        # Validate Redis URL format
        if not self.redis.url.startswith('redis://'):
            errors.append("Invalid REDIS_URL format")
        
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_message)
    
    def _setup_logging(self) -> None:
        """Setup application logging"""
        log_level = getattr(logging, self.monitoring.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == 'development'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == 'production'
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.testing or self.environment == 'testing'
    
    def get_redis_client(self) -> redis.Redis:
        """Get configured Redis client"""
        return redis.from_url(
            self.redis.url,
            max_connections=self.redis.max_connections,
            retry_on_timeout=self.redis.retry_on_timeout,
            health_check_interval=self.redis.health_check_interval
        )
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy database configuration"""
        return {
            'SQLALCHEMY_DATABASE_URI': self.database.url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': self.database.pool_size,
                'pool_timeout': self.database.pool_timeout,
                'pool_recycle': self.database.pool_recycle,
                'max_overflow': self.database.max_overflow,
                'echo': self.database.echo if self.is_development else False
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive data)"""
        sensitive_keys = {'secret_key', 'jwt_secret_key', 'client_secret', 'smtp_password', 'openai_api_key', 'encryption_key'}
        
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            
            if hasattr(value, '__dict__'):  # dataclass
                section_dict = {}
                for sub_key, sub_value in value.__dict__.items():
                    if sub_key.lower() in sensitive_keys:
                        section_dict[sub_key] = '***' if sub_value else None
                    else:
                        section_dict[sub_key] = sub_value
                result[key] = section_dict
            else:
                if key.lower() in sensitive_keys:
                    result[key] = '***' if value else None
                else:
                    result[key] = value
        
        return result

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Returns:
        Singleton Settings instance
    """
    return Settings()

# Convenience accessors
def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    return get_settings().get_database_config()

def get_redis_client() -> redis.Redis:
    """Get Redis client"""
    return get_settings().get_redis_client()

def get_google_config() -> GoogleConfig:
    """Get Google API configuration"""
    return get_settings().google

def get_microsoft_config() -> MicrosoftConfig:
    """Get Microsoft Graph configuration"""
    return get_settings().microsoft
