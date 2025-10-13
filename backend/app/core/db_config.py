"""
Production-Ready Database Configuration

This module provides comprehensive database configuration including:
- Connection pooling optimization
- Read/write database separation
- Transaction isolation levels
- Performance monitoring settings
- Migration validation
- Backup verification
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class TransactionIsolationLevel(Enum):
    """Database transaction isolation levels."""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"

class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"

@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration for production databases."""
    
    # Core pool settings
    pool_size: int = field(default_factory=lambda: int(os.getenv('DB_POOL_SIZE', '20')))
    max_overflow: int = field(default_factory=lambda: int(os.getenv('DB_MAX_OVERFLOW', '30')))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv('DB_POOL_TIMEOUT', '30')))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv('DB_POOL_RECYCLE', '3600')))
    
    # Advanced pool settings
    pool_pre_ping: bool = field(default_factory=lambda: os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true')
    pool_reset_on_return: str = field(default_factory=lambda: os.getenv('DB_POOL_RESET_ON_RETURN', 'commit'))
    pool_use_lifo: bool = field(default_factory=lambda: os.getenv('DB_POOL_USE_LIFO', 'false').lower() == 'true')
    
    # Connection validation
    pool_validation_interval: int = field(default_factory=lambda: int(os.getenv('DB_POOL_VALIDATION_INTERVAL', '300')))
    pool_echo_pool: bool = field(default_factory=lambda: os.getenv('DB_POOL_ECHO_POOL', 'false').lower() == 'true')
    
    # Performance tuning
    pool_overflow_timeout: int = field(default_factory=lambda: int(os.getenv('DB_POOL_OVERFLOW_TIMEOUT', '60')))
    pool_overflow_shutdown: bool = field(default_factory=lambda: os.getenv('DB_POOL_OVERFLOW_SHUTDOWN', 'false').lower() == 'true')

@dataclass
class DatabaseConnectionConfig:
    """Individual database connection configuration."""
    
    url: str
    name: str
    role: str = "read_write"  # read_only, read_write, backup
    weight: int = 1  # Load balancing weight
    
    # Connection settings
    connect_timeout: int = field(default_factory=lambda: int(os.getenv('DB_CONNECT_TIMEOUT', '10')))
    command_timeout: int = field(default_factory=lambda: int(os.getenv('DB_COMMAND_TIMEOUT', '30')))
    application_name: str = field(default_factory=lambda: os.getenv('DB_APPLICATION_NAME', 'automated_report_platform'))
    
    # SSL configuration
    ssl_mode: str = field(default_factory=lambda: os.getenv('DB_SSL_MODE', 'prefer'))
    ssl_cert: Optional[str] = field(default_factory=lambda: os.getenv('DB_SSL_CERT'))
    ssl_key: Optional[str] = field(default_factory=lambda: os.getenv('DB_SSL_KEY'))
    ssl_ca: Optional[str] = field(default_factory=lambda: os.getenv('DB_SSL_CA'))
    
    # Connection limits
    max_connections: int = field(default_factory=lambda: int(os.getenv('DB_MAX_CONNECTIONS', '100')))
    min_connections: int = field(default_factory=lambda: int(os.getenv('DB_MIN_CONNECTIONS', '5')))
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.url:
            raise ValueError(f"Database URL is required for {self.name}")
        
        if self.role not in ["read_only", "read_write", "backup"]:
            raise ValueError(f"Invalid database role: {self.role}")
        
        if self.weight < 1:
            raise ValueError(f"Database weight must be >= 1 for {self.name}")

@dataclass
class DatabasePerformanceConfig:
    """Database performance monitoring and optimization configuration."""
    
    # Query monitoring
    enable_query_logging: bool = field(default_factory=lambda: os.getenv('DB_ENABLE_QUERY_LOGGING', 'false').lower() == 'true')
    slow_query_threshold_ms: int = field(default_factory=lambda: int(os.getenv('DB_SLOW_QUERY_THRESHOLD_MS', '1000')))
    max_query_log_size: int = field(default_factory=lambda: int(os.getenv('DB_MAX_QUERY_LOG_SIZE', '1000')))
    
    # Performance metrics
    enable_performance_metrics: bool = field(default_factory=lambda: os.getenv('DB_ENABLE_PERFORMANCE_METRICS', 'true').lower() == 'true')
    metrics_collection_interval: int = field(default_factory=lambda: int(os.getenv('DB_METRICS_COLLECTION_INTERVAL', '60')))
    
    # Connection monitoring
    enable_connection_monitoring: bool = field(default_factory=lambda: os.getenv('DB_ENABLE_CONNECTION_MONITORING', 'true').lower() == 'true')
    connection_health_check_interval: int = field(default_factory=lambda: int(os.getenv('DB_CONNECTION_HEALTH_CHECK_INTERVAL', '300')))
    
    # Query optimization
    enable_query_plan_analysis: bool = field(default_factory=lambda: os.getenv('DB_ENABLE_QUERY_PLAN_ANALYSIS', 'false').lower() == 'true')
    enable_statistics_collection: bool = field(default_factory=lambda: os.getenv('DB_ENABLE_STATISTICS_COLLECTION', 'true').lower() == 'true')

@dataclass
class DatabaseMigrationConfig:
    """Database migration and schema management configuration."""
    
    # Migration settings
    auto_migrate: bool = field(default_factory=lambda: os.getenv('DB_AUTO_MIGRATE', 'false').lower() == 'true')
    migration_validation: bool = field(default_factory=lambda: os.getenv('DB_MIGRATION_VALIDATION', 'true').lower() == 'true')
    migration_timeout: int = field(default_factory=lambda: int(os.getenv('DB_MIGRATION_TIMEOUT', '300')))
    
    # Schema validation
    validate_schema_on_startup: bool = field(default_factory=lambda: os.getenv('DB_VALIDATE_SCHEMA_ON_STARTUP', 'true').lower() == 'true')
    schema_version_check: bool = field(default_factory=lambda: os.getenv('DB_SCHEMA_VERSION_CHECK', 'true').lower() == 'true')
    
    # Backup verification
    enable_backup_verification: bool = field(default_factory=lambda: os.getenv('DB_ENABLE_BACKUP_VERIFICATION', 'true').lower() == 'true')
    backup_verification_interval: int = field(default_factory=lambda: int(os.getenv('DB_BACKUP_VERIFICATION_INTERVAL', '86400')))  # 24 hours

@dataclass
class DatabaseSecurityConfig:
    """Database security configuration."""
    
    # Connection security
    require_ssl: bool = field(default_factory=lambda: os.getenv('DB_REQUIRE_SSL', 'false').lower() == 'true')
    ssl_verify_mode: str = field(default_factory=lambda: os.getenv('DB_SSL_VERIFY_MODE', 'optional'))
    
    # Authentication
    connection_encryption: bool = field(default_factory=lambda: os.getenv('DB_CONNECTION_ENCRYPTION', 'false').lower() == 'true')
    password_encryption: bool = field(default_factory=lambda: os.getenv('DB_PASSWORD_ENCRYPTION', 'false').lower() == 'true')
    
    # Access control
    connection_limit_per_user: int = field(default_factory=lambda: int(os.getenv('DB_CONNECTION_LIMIT_PER_USER', '10')))
    max_failed_connections: int = field(default_factory=lambda: int(os.getenv('DB_MAX_FAILED_CONNECTIONS', '3')))

class ProductionDatabaseConfig:
    """
    Production-ready database configuration manager.
    
    Features:
    - Multiple database support (read/write separation)
    - Connection pooling optimization
    - Performance monitoring
    - Migration validation
    - Security configuration
    """
    
    def __init__(self):
        self.environment = os.getenv('FLASK_ENV', 'development')
        self.database_type = self._detect_database_type()
        
        # Initialize configuration sections
        self.connection_pool = ConnectionPoolConfig()
        self.performance = DatabasePerformanceConfig()
        self.migration = DatabaseMigrationConfig()
        self.security = DatabaseSecurityConfig()
        
        # Database connections
        self.primary_database = self._create_primary_database_config()
        self.read_replicas = self._create_read_replica_configs()
        self.backup_database = self._create_backup_database_config()
        
        # Validate configuration only if not in development mode
        if self.environment != 'development':
            self._validate_configuration()
    
    def _detect_database_type(self) -> DatabaseType:
        """Detect database type from environment."""
        database_url = os.getenv('DATABASE_URL', '')
        
        # Debug: Print what we're detecting
        print(f"DEBUG: DATABASE_URL from environment: '{database_url}'")
        print(f"DEBUG: FLASK_ENV from environment: '{os.getenv('FLASK_ENV', 'not_set')}'")
        
        # Allow PostgreSQL in development for testing
        # if os.getenv('FLASK_ENV') == 'development':
        #     print("DEBUG: Development mode - forcing SQLite")
        #     return DatabaseType.SQLITE
        
        # Production mode - detect from DATABASE_URL
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            print("DEBUG: Detected PostgreSQL")
            return DatabaseType.POSTGRESQL
        elif database_url.startswith('mysql://'):
            print("DEBUG: Detected MySQL")
            return DatabaseType.MYSQL
        elif database_url.startswith('sqlite://'):
            print("DEBUG: Detected SQLite")
            return DatabaseType.SQLITE
        else:
            print(f"DEBUG: Unknown database URL format, defaulting to SQLite: '{database_url}'")
            logger.warning(f"Unknown database URL format: {database_url}")
            return DatabaseType.SQLITE
    
    def _create_primary_database_config(self) -> DatabaseConnectionConfig:
        """Create primary database configuration."""
        # Use DATABASE_URL from environment
        database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
        print(f"DEBUG: Using DATABASE_URL: {database_url}")
        
        return DatabaseConnectionConfig(
            url=database_url,
            name="primary",
            role="read_write",
            weight=10,  # Highest weight for primary
            ssl_mode=os.getenv('DB_PRIMARY_SSL_MODE', 'require') if self.environment == 'production' else 'prefer',
            ssl_cert=os.getenv('DB_PRIMARY_SSL_CERT'),
            ssl_key=os.getenv('DB_PRIMARY_SSL_KEY'),
            ssl_ca=os.getenv('DB_PRIMARY_SSL_CA')
        )
    
    def _create_read_replica_configs(self) -> List[DatabaseConnectionConfig]:
        """Create read replica configurations."""
        read_replicas = []
        
        # Parse comma-separated read replica URLs
        replica_urls = os.getenv('DB_READ_REPLICA_URLS', '').split(',')
        
        for i, url in enumerate(replica_urls):
            url = url.strip()
            if url:
                replica_config = DatabaseConnectionConfig(
                    url=url,
                    name=f"read_replica_{i+1}",
                    role="read_only",
                    weight=int(os.getenv(f'DB_READ_REPLICA_{i+1}_WEIGHT', '5')),
                    ssl_mode=os.getenv(f'DB_READ_REPLICA_{i+1}_SSL_MODE', 'prefer'),
                    ssl_cert=os.getenv(f'DB_READ_REPLICA_{i+1}_SSL_CERT'),
                    ssl_key=os.getenv(f'DB_READ_REPLICA_{i+1}_SSL_KEY'),
                    ssl_ca=os.getenv(f'DB_READ_REPLICA_{i+1}_SSL_CA')
                )
                read_replicas.append(replica_config)
        
        return read_replicas
    
    def _create_backup_database_config(self) -> Optional[DatabaseConnectionConfig]:
        """Create backup database configuration."""
        backup_url = os.getenv('DB_BACKUP_URL')
        
        if not backup_url:
            return None
        
        return DatabaseConnectionConfig(
            url=backup_url,
            name="backup",
            role="backup",
            weight=1,
            ssl_mode=os.getenv('DB_BACKUP_SSL_MODE', 'require'),
            ssl_cert=os.getenv('DB_BACKUP_SSL_CERT'),
            ssl_key=os.getenv('DB_BACKUP_SSL_KEY'),
            ssl_ca=os.getenv('DB_BACKUP_SSL_CA')
        )
    
    def _validate_configuration(self):
        """Validate the complete database configuration."""
        errors = []
        
        # Validate primary database
        if not self.primary_database.url:
            errors.append("Primary database URL is required")
        
        # Validate SSL configuration for production
        if self.environment == 'production':
            if self.database_type in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL]:
                if not self.security.require_ssl:
                    errors.append("SSL is required for production databases")
                
                if not self.primary_database.ssl_ca:
                    errors.append("SSL CA certificate is required for production")
        
        # Validate connection pool settings
        if self.connection_pool.pool_size < 1:
            errors.append("Connection pool size must be >= 1")
        
        if self.connection_pool.max_overflow < 0:
            errors.append("Max overflow must be >= 0")
        
        # Validate read replicas
        for replica in self.read_replicas:
            if replica.role != "read_only":
                errors.append(f"Read replica {replica.name} must have read_only role")
        
        if errors:
            error_message = "Database configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_message)
    
    def get_sqlalchemy_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy configuration for Flask-SQLAlchemy."""
        config = {
            'SQLALCHEMY_DATABASE_URI': self.primary_database.url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': self.connection_pool.pool_size,
                'max_overflow': self.connection_pool.max_overflow,
                'pool_timeout': self.connection_pool.pool_timeout,
                'pool_recycle': self.connection_pool.pool_recycle,
                'pool_pre_ping': self.connection_pool.pool_pre_ping,
                'echo_pool': self.connection_pool.pool_echo_pool,
                'connect_args': self._get_connection_args()
            }
        }
        
        # Add database-specific options
        if self.database_type == DatabaseType.POSTGRESQL:
            # PostgreSQL supports more pool options
            config['SQLALCHEMY_ENGINE_OPTIONS'].update({
                'pool_reset_on_return': self.connection_pool.pool_reset_on_return,
                'pool_use_lifo': self.connection_pool.pool_use_lifo,
                # 'pool_validation_interval': self.connection_pool.pool_validation_interval,  # Not supported by SQLAlchemy
            })
            
            config['SQLALCHEMY_ENGINE_OPTIONS']['connect_args'].update({
                'application_name': self.primary_database.application_name,
                'connect_timeout': self.primary_database.connect_timeout,
                # 'command_timeout': self.primary_database.command_timeout,  # Not supported by psycopg2
                'sslmode': self.primary_database.ssl_mode
            })
        
        elif self.database_type == DatabaseType.MYSQL:
            # MySQL supports some pool options
            config['SQLALCHEMY_ENGINE_OPTIONS'].update({
                'pool_reset_on_return': self.connection_pool.pool_reset_on_return,
            })
        
        # SQLite has limited pool support, so we only include basic options
        if self.database_type == DatabaseType.SQLITE:
            # SQLite doesn't support connection pooling in the same way
            # Override with SQLite-appropriate settings
            config['SQLALCHEMY_ENGINE_OPTIONS'].update({
                'pool_size': 1,  # SQLite works best with single connection
                'max_overflow': 0,  # No overflow for SQLite
                'pool_recycle': -1,  # Don't recycle SQLite connections
                'pool_pre_ping': False,  # Not needed for SQLite
                'pool_timeout': 30,  # Use a reasonable timeout for SQLite
            })
        
        return config
    
    def _get_connection_args(self) -> Dict[str, Any]:
        """Get database-specific connection arguments."""
        args = {}
        
        if self.database_type == DatabaseType.POSTGRESQL:
            args.update({
                'connect_timeout': self.primary_database.connect_timeout,
                'application_name': self.primary_database.application_name
            })
            
            # Add SSL configuration
            if self.primary_database.ssl_cert:
                args['sslcert'] = self.primary_database.ssl_cert
            if self.primary_database.ssl_key:
                args['sslkey'] = self.primary_database.ssl_key
            if self.primary_database.ssl_ca:
                args['sslrootcert'] = self.primary_database.ssl_ca
        
        elif self.database_type == DatabaseType.MYSQL:
            args.update({
                'connect_timeout': self.primary_database.connect_timeout,
                'charset': 'utf8mb4',
                'autocommit': False
            })
        
        elif self.database_type == DatabaseType.SQLITE:
            args.update({
                'timeout': self.primary_database.connect_timeout,
                'check_same_thread': False
            })
        
        return args
    
    def get_read_replica_urls(self) -> List[str]:
        """Get list of read replica URLs for load balancing."""
        return [replica.url for replica in self.read_replicas]
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information."""
        return {
            'database_type': self.database_type.value,
            'environment': self.environment,
            'primary_database': {
                'name': self.primary_database.name,
                'role': self.primary_database.role,
                'host': self._extract_host_from_url(self.primary_database.url),
                'database': self._extract_database_from_url(self.primary_database.url),
                'ssl_enabled': bool(self.primary_database.ssl_cert or self.primary_database.ssl_ca)
            },
            'read_replicas': [
                {
                    'name': replica.name,
                    'role': replica.role,
                    'host': self._extract_host_from_url(replica.url),
                    'weight': replica.weight
                }
                for replica in self.read_replicas
            ],
            'backup_database': {
                'name': self.backup_database.name,
                'role': self.backup_database.role,
                'host': self._extract_host_from_url(self.backup_database.url)
            } if self.backup_database else None,
            'connection_pool': {
                'pool_size': self.connection_pool.pool_size,
                'max_overflow': self.connection_pool.max_overflow,
                'pool_timeout': self.connection_pool.pool_timeout,
                'pool_recycle': self.connection_pool.pool_recycle
            },
            'performance': {
                'enable_query_logging': self.performance.enable_query_logging,
                'slow_query_threshold_ms': self.performance.slow_query_threshold_ms,
                'enable_performance_metrics': self.performance.enable_performance_metrics
            },
            'migration': {
                'auto_migrate': self.migration.auto_migrate,
                'validate_schema_on_startup': self.migration.validate_schema_on_startup,
                'enable_backup_verification': self.migration.enable_backup_verification
            },
            'security': {
                'require_ssl': self.security.require_ssl,
                'connection_encryption': self.security.connection_encryption,
                'ssl_verify_mode': self.security.ssl_verify_mode
            }
        }
    
    def _extract_host_from_url(self, url: str) -> str:
        """Extract host from database URL."""
        try:
            parsed = urlparse(url)
            return parsed.hostname or 'localhost'
        except Exception:
            return 'unknown'
    
    def _extract_database_from_url(self, url: str) -> str:
        """Extract database name from database URL."""
        try:
            parsed = urlparse(url)
            return parsed.path[1:] if parsed.path else 'unknown'
        except Exception:
            return 'unknown'
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == 'production'
    
    def supports_read_replicas(self) -> bool:
        """Check if read replicas are configured."""
        return len(self.read_replicas) > 0
    
    def get_optimal_read_database(self) -> DatabaseConnectionConfig:
        """Get the optimal read database (primary or replica)."""
        if not self.read_replicas:
            return self.primary_database
        
        # Simple round-robin selection (can be enhanced with health checks)
        # For now, return the first available replica
        return self.read_replicas[0]

# Global configuration instance - created lazily to avoid validation issues
_db_config_instance = None

def get_database_config() -> ProductionDatabaseConfig:
    """Get the global database configuration instance."""
    global _db_config_instance
    if _db_config_instance is None:
        _db_config_instance = ProductionDatabaseConfig()
    return _db_config_instance

def get_sqlalchemy_config() -> Dict[str, Any]:
    """Get SQLAlchemy configuration for Flask-SQLAlchemy."""
    return get_database_config().get_sqlalchemy_config()

def get_database_info() -> Dict[str, Any]:
    """Get comprehensive database information."""
    return get_database_config().get_database_info()
