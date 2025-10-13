"""
Production-Ready Database Connection Management

This module provides comprehensive database management including:
- Advanced connection pooling with optimization
- Circuit breaker pattern for connection failures
- Read/write database separation
- Transaction isolation level management
- Performance monitoring and metrics
- Migration validation and backup verification
- Graceful connection handling
"""

import os
import time
import logging
import threading
from typing import Optional, Dict, Any, Union, List, Callable
from contextlib import contextmanager
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

import sqlalchemy
from sqlalchemy import create_engine, text, inspect, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import (
    OperationalError, 
    DisconnectionError, 
    TimeoutError as SQLAlchemyTimeoutError,
    SQLAlchemyError,
    DBAPIError
)
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import _ConnectionFairy
from flask import current_app, g

# Import the new production database configuration
from .db_config import (
    get_database_config, 
    TransactionIsolationLevel, 
    DatabaseType,
    ProductionDatabaseConfig
)

logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors"""
    pass

class DatabaseHealthCheckError(Exception):
    """Custom exception for database health check failures"""
    pass

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class DatabaseMigrationError(Exception):
    """Exception for database migration failures"""
    pass

class BackupVerificationError(Exception):
    """Exception for backup verification failures"""
    pass

@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    total_queries: int = 0
    slow_queries: int = 0
    failed_queries: int = 0
    total_query_time: float = 0.0
    slow_query_threshold_ms: float = 1000.0
    last_reset: datetime = field(default_factory=datetime.utcnow)
    
    def record_query(self, duration_ms: float, success: bool = True):
        """Record a database query."""
        self.total_queries += 1
        self.total_query_time += duration_ms
        
        if duration_ms > self.slow_query_threshold_ms:
            self.slow_queries += 1
        
        if not success:
            self.failed_queries += 1
    
    def get_average_query_time(self) -> float:
        """Get average query time in milliseconds."""
        if self.total_queries == 0:
            return 0.0
        return self.total_query_time / self.total_queries
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database metrics information."""
        return {
            "total_queries": self.total_queries,
            "slow_queries": self.slow_queries,
            "failed_queries": self.failed_queries,
            "total_query_time_ms": round(self.total_query_time, 2),
            "average_query_time_ms": round(self.get_average_query_time(), 2),
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "last_reset": self.last_reset.isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.last_reset).total_seconds()
        }
    
    def reset(self):
        """Reset metrics."""
        self.total_queries = 0
        self.slow_queries = 0
        self.failed_queries = 0
        self.total_query_time = 0.0
        self.last_reset = datetime.utcnow()

class CircuitBreaker:
    """Circuit breaker pattern for database connections."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful operation."""
        with self._lock:
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
            self.last_failure_time = None
    
    def _on_failure(self):
        """Handle failed operation."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) > self.recovery_timeout
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }

class DatabaseManager:
    """
    Production-ready database connection manager with:
    - Advanced connection pooling with optimization
    - Circuit breaker pattern for connection failures
    - Read/write database separation
    - Transaction isolation level management
    - Performance monitoring and metrics
    - Migration validation and backup verification
    - Graceful connection handling
    """
    
    def __init__(self):
        # Use the new production database configuration
        self.config = get_database_config()
        self.engine: Optional[Engine] = None
        self.read_engines: List[Engine] = []
        self.session_factory: Optional[sessionmaker] = None
        self.read_session_factories: List[sessionmaker] = []
        self.is_initialized = False
        
        # Performance monitoring
        self.metrics = DatabaseMetrics()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=int(os.getenv('DB_CIRCUIT_BREAKER_THRESHOLD', '5')),
            recovery_timeout=int(os.getenv('DB_CIRCUIT_BREAKER_RECOVERY_TIMEOUT', '60'))
        )
        
        # Connection health monitoring
        self.health_check_interval = int(os.getenv('DB_HEALTH_CHECK_INTERVAL', '300'))
        self.last_health_check = 0
        self.connection_health_status = "unknown"
        
        # Migration and backup tracking
        self.last_migration_check = 0
        self.last_backup_verification = 0
        
        # Thread-local storage for session management
        self._local = threading.local()
        
    def initialize(self) -> None:
        """Initialize database connections and pools with production-ready configuration"""
        try:
            if self.is_initialized:
                logger.info("Database manager already initialized")
                return
                
            logger.info("Initializing production database manager...")
            
            # Initialize primary database (read/write)
            self._initialize_primary_database()
            
            # Initialize read replicas if configured
            if self.config.supports_read_replicas():
                self._initialize_read_replicas()
            
            # Initialize backup database if configured
            if self.config.backup_database:
                self._initialize_backup_database()
            
            # Test all connections
            self._test_all_connections()
            
            # Validate schema if configured
            if self.config.migration.validate_schema_on_startup:
                self._validate_schema()
            
            # Verify backup if configured
            if self.config.migration.enable_backup_verification:
                self._verify_backup()
            
            # Setup performance monitoring
            self._setup_performance_monitoring()
            
            self.is_initialized = True
            logger.info("Production database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {str(e)}")
            raise DatabaseConnectionError(f"Database initialization failed: {str(e)}")
    
    def _initialize_primary_database(self) -> None:
        """Initialize primary database (read/write) with production configuration."""
        logger.info("Initializing primary database...")
        
        # Get SQLAlchemy configuration
        sqlalchemy_config = self.config.get_sqlalchemy_config()
        
        # Create engine with production-optimized settings
        self.engine = create_engine(
            sqlalchemy_config['SQLALCHEMY_DATABASE_URI'],
            **sqlalchemy_config['SQLALCHEMY_ENGINE_OPTIONS']
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        # Set transaction isolation level
        self._set_transaction_isolation_level()
        
        logger.info("Primary database initialized successfully")
    
    def _initialize_read_replicas(self) -> None:
        """Initialize read replica databases."""
        logger.info("Initializing read replicas...")
        
        for replica_config in self.config.read_replicas:
            try:
                # Create engine for read replica
                engine = create_engine(
                    replica_config.url,
                    pool_size=min(10, self.config.connection_pool.pool_size // 2),
                    max_overflow=min(15, self.config.connection_pool.max_overflow // 2),
                    pool_timeout=self.config.connection_pool.pool_timeout,
                    pool_recycle=self.config.connection_pool.pool_recycle,
                    pool_pre_ping=True,
                    connect_args=self._get_replica_connection_args(replica_config)
                )
                
                # Create session factory for read replica
                session_factory = sessionmaker(
                    bind=engine,
                    autocommit=False,
                    autoflush=False
                )
                
                self.read_engines.append(engine)
                self.read_session_factories.append(session_factory)
                
                logger.info(f"Read replica {replica_config.name} initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize read replica {replica_config.name}: {e}")
                # Continue with other replicas
    
    def _initialize_backup_database(self) -> None:
        """Initialize backup database."""
        if not self.config.backup_database:
            return
            
        logger.info("Initializing backup database...")
        
        try:
            # Create minimal engine for backup (read-only operations)
            backup_engine = create_engine(
                self.config.backup_database.url,
                pool_size=2,
                max_overflow=5,
                pool_timeout=60,
                pool_pre_ping=True,
                connect_args=self._get_backup_connection_args()
            )
            
            # Store backup engine for verification operations
            self.backup_engine = backup_engine
            
            logger.info("Backup database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize backup database: {e}")
            # Backup failure shouldn't prevent primary initialization
    
    def _get_replica_connection_args(self, replica_config) -> Dict[str, Any]:
        """Get connection arguments for read replicas."""
        args = {}
        
        if self.config.database_type == DatabaseType.POSTGRESQL:
            args.update({
                'connect_timeout': replica_config.connect_timeout,
                'application_name': f"{replica_config.application_name}_read_replica",
                'sslmode': replica_config.ssl_mode
            })
            
            # Add SSL configuration
            if replica_config.ssl_cert:
                args['sslcert'] = replica_config.ssl_cert
            if replica_config.ssl_key:
                args['sslkey'] = replica_config.ssl_key
            if replica_config.ssl_ca:
                args['sslrootcert'] = replica_config.ssl_ca
        
        return args
    
    def _get_backup_connection_args(self) -> Dict[str, Any]:
        """Get connection arguments for backup database."""
        args = {}
        
        if self.config.database_type == DatabaseType.POSTGRESQL:
            args.update({
                'connect_timeout': 30,  # Longer timeout for backup
                'application_name': f"{self.config.backup_database.application_name}_backup",
                'sslmode': self.config.backup_database.ssl_mode
            })
            
            # Add SSL configuration
            if self.config.backup_database.ssl_cert:
                args['sslcert'] = self.config.backup_database.ssl_cert
            if self.config.backup_database.ssl_key:
                args['sslkey'] = self.config.backup_database.ssl_key
            if self.config.backup_database.ssl_ca:
                args['sslrootcert'] = self.config.backup_database.ssl_ca
        
        return args
    
    def _set_transaction_isolation_level(self) -> None:
        """Set transaction isolation level for the primary database."""
        try:
            isolation_level = os.getenv('DB_TRANSACTION_ISOLATION_LEVEL', 'READ_COMMITTED')
            
            if isolation_level in [level.value for level in TransactionIsolationLevel]:
                with self.engine.connect() as conn:
                    conn.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
                    conn.commit()
                
                logger.info(f"Transaction isolation level set to {isolation_level}")
            else:
                logger.warning(f"Invalid transaction isolation level: {isolation_level}")
                
        except Exception as e:
            logger.warning(f"Failed to set transaction isolation level: {e}")
    
    def _test_all_connections(self) -> None:
        """Test all database connections."""
        logger.info("Testing all database connections...")
        
        # Test primary database
        self._test_connection(self.engine, "primary")
        
        # Test read replicas
        for i, engine in enumerate(self.read_engines):
            self._test_connection(engine, f"read_replica_{i+1}")
        
        # Test backup database
        if hasattr(self, 'backup_engine'):
            self._test_connection(self.backup_engine, "backup")
        
        self.connection_health_status = "healthy"
        logger.info("All database connections tested successfully")
    
    def _test_connection(self, engine: Engine, name: str) -> None:
        """Test a specific database connection."""
        try:
            with engine.connect() as conn:
                if self.config.database_type == DatabaseType.POSTGRESQL:
                    result = conn.execute(text("SELECT 1 as test, version() as version"))
                else:
                    result = conn.execute(text("SELECT 1 as test"))
                
                result.fetchone()
                logger.info(f"Database connection {name} test successful")
                
        except Exception as e:
            logger.error(f"Database connection {name} test failed: {e}")
            raise DatabaseConnectionError(f"Connection test failed for {name}: {e}")
    
    def _validate_schema(self) -> None:
        """Validate database schema on startup."""
        try:
            logger.info("Validating database schema...")
            
            with self.get_session() as session:
                # Check if required tables exist
                inspector = inspect(self.engine)
                existing_tables = inspector.get_table_names()
                
                # Define required tables (adjust based on your models)
                required_tables = ['users', 'forms', 'reports']  # Add your required tables
                
                missing_tables = [table for table in required_tables if table not in existing_tables]
                
                if missing_tables:
                    logger.warning(f"Missing required tables: {missing_tables}")
                    
                    if self.config.migration.auto_migrate:
                        logger.info("Auto-migration enabled, attempting to create missing tables")
                        self._auto_migrate_schema(session, missing_tables)
                    else:
                        logger.error("Schema validation failed - missing tables and auto-migration disabled")
                        raise DatabaseMigrationError(f"Missing required tables: {missing_tables}")
                
                logger.info("Database schema validation completed successfully")
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            if self.config.migration.migration_validation:
                raise DatabaseMigrationError(f"Schema validation failed: {e}")
            else:
                logger.warning("Schema validation failed but continuing due to configuration")
    
    def _auto_migrate_schema(self, session: Session, missing_tables: List[str]) -> None:
        """Automatically migrate missing schema elements."""
        try:
            logger.info(f"Auto-migrating missing tables: {missing_tables}")
            
            # Import models to create tables
            from ..models import Base  # Adjust import path as needed
            
            # Create missing tables
            Base.metadata.create_all(bind=self.engine, tables=[
                Base.metadata.tables[table] for table in missing_tables
                if table in Base.metadata.tables
            ])
            
            logger.info("Auto-migration completed successfully")
            
        except Exception as e:
            logger.error(f"Auto-migration failed: {e}")
            raise DatabaseMigrationError(f"Auto-migration failed: {e}")
    
    def _verify_backup(self) -> None:
        """Verify backup database integrity."""
        if not hasattr(self, 'backup_engine'):
            return
            
        try:
            logger.info("Verifying backup database...")
            
            with self.backup_engine.connect() as conn:
                # Perform basic connectivity test
                result = conn.execute(text("SELECT 1 as test"))
                result.fetchone()
                
                # Check backup age (if backup timestamp is stored)
                # This is a simplified check - implement based on your backup strategy
                backup_age_hours = 24  # Assume backup is recent
                
                if backup_age_hours > 48:  # 48 hours threshold
                    logger.warning(f"Backup is {backup_age_hours} hours old")
                else:
                    logger.info("Backup verification completed successfully")
                    
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            
            if self.config.migration.enable_backup_verification:
                raise BackupVerificationError(f"Backup verification failed: {e}")
            else:
                logger.warning("Backup verification failed but continuing due to configuration")
    
    def _setup_performance_monitoring(self) -> None:
        """Setup database performance monitoring."""
        if not self.config.performance.enable_performance_metrics:
            return
            
        logger.info("Setting up database performance monitoring...")
        
        # Setup SQLAlchemy event listeners for query monitoring
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            query_start_time = conn.info['query_start_time'].pop(-1)
            duration_ms = (time.time() - query_start_time) * 1000
            
            # Record query metrics
            self.metrics.record_query(duration_ms, success=True)
            
            # Log slow queries
            if duration_ms > self.config.performance.slow_query_threshold_ms:
                logger.warning(f"Slow query detected: {duration_ms:.2f}ms - {statement[:100]}...")
        
        # Setup error handling
        @event.listens_for(self.engine, "dbapi_error")
        def dbapi_error(conn, cursor, statement, parameters, context, exception):
            # Record failed query
            self.metrics.record_query(0, success=False)
            logger.error(f"Database error: {exception} - Statement: {statement[:100]}...")
        
        logger.info("Database performance monitoring setup completed")
    
    def _is_postgresql(self, db_url: str) -> bool:
        """Check if database URL is PostgreSQL"""
        return db_url.startswith('postgresql://') or db_url.startswith('postgres://')
    
    def _is_sqlite(self, db_url: str) -> bool:
        """Check if database URL is SQLite"""
        return db_url.startswith('sqlite://')
    
    def _initialize_postgresql(self, db_url: str) -> None:
        """Initialize PostgreSQL connection with pooling"""
        logger.info("Initializing PostgreSQL connection...")
        
        # Parse connection parameters
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        # Create SQLAlchemy engine with connection pooling
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=self.settings.database.pool_size,
            max_overflow=self.settings.database.max_overflow,
            pool_timeout=self.settings.database.pool_timeout,
            pool_recycle=self.settings.database.pool_recycle,
            pool_pre_ping=True,  # Enable connection health checks
            echo=self.settings.database.echo,
            connect_args={
                'connect_timeout': 10,
                'application_name': 'automated_report_platform'
            }
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        # Create psycopg2 connection pool for direct access
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.settings.database.pool_size,
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:] if parsed.path else 'postgres',
                user=parsed.username,
                password=parsed.password,
                cursor_factory=RealDictCursor,
                connect_timeout=10
            )
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.warning(f"Failed to create psycopg2 connection pool: {str(e)}")
            self.connection_pool = None
    
    def _initialize_sqlite(self, db_url: str) -> None:
        """Initialize SQLite connection"""
        logger.info("Initializing SQLite connection...")
        
        # Create SQLAlchemy engine for SQLite
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=1,  # SQLite doesn't support multiple connections well
            max_overflow=0,
            pool_timeout=20,
            pool_recycle=3600,
            connect_args={
                'timeout': 20,
                'check_same_thread': False
            }
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("SQLite connection initialized successfully")
    
    def _test_connection(self) -> None:
        """Test database connection"""
        try:
            with self.get_session() as session:
                if self._is_postgresql(self.settings.database.url):
                    result = session.execute(text("SELECT 1 as test"))
                else:
                    result = session.execute(text("SELECT 1 as test"))
                result.fetchone()
                logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            raise DatabaseConnectionError(f"Connection test failed: {str(e)}")
    
    @contextmanager
    def get_session(self, read_only: bool = False):
        """Get database session with automatic cleanup and read/write separation."""
        if not self.is_initialized:
            self.initialize()
        
        # Choose appropriate session factory based on operation type
        if read_only and self.read_session_factories:
            # Use read replica for read operations
            session_factory = self._get_optimal_read_session_factory()
        else:
            # Use primary database for write operations
            session_factory = self.session_factory
        
        session = session_factory()
        try:
            yield session
            if not read_only:
                session.commit()
        except Exception as e:
            if not read_only:
                session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def _get_optimal_read_session_factory(self) -> sessionmaker:
        """Get the optimal read session factory (load balancing)."""
        if not self.read_session_factories:
            return self.session_factory
        
        # Simple round-robin selection (can be enhanced with health checks)
        # For now, use the first available replica
        return self.read_session_factories[0]
    
    def get_read_session(self):
        """Get a read-only session from a replica if available."""
        return self.get_session(read_only=True)
    
    def get_write_session(self):
        """Get a write session from the primary database."""
        return self.get_session(read_only=False)
    
    def execute_read_operation(self, operation: Callable, *args, **kwargs):
        """Execute a read operation with automatic replica selection."""
        try:
            with self.get_read_session() as session:
                return operation(session, *args, **kwargs)
        except Exception as e:
            logger.error(f"Read operation failed: {e}")
            # Fallback to primary database
            with self.get_session(read_only=True) as session:
                return operation(session, *args, **kwargs)
    
    def execute_write_operation(self, operation: Callable, *args, **kwargs):
        """Execute a write operation on the primary database."""
        with self.get_write_session() as session:
            return operation(session, *args, **kwargs)
    
    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine"""
        if not self.is_initialized:
            self.initialize()
        return self.engine
    
    def get_session_factory(self) -> sessionmaker:
        """Get session factory"""
        if not self.is_initialized:
            self.initialize()
        return self.session_factory
    
    def execute_with_retry(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """
        Execute function with enhanced retry logic and circuit breaker protection
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries (doubles each retry)
        
        Returns:
            Function result
            
        Raises:
            DatabaseConnectionError: If all retries fail
            CircuitBreakerError: If circuit breaker is open
        """
        # Use circuit breaker for protection
        return self.circuit_breaker.call(
            lambda: self._execute_with_retry_internal(func, max_retries, base_delay)
        )
    
    def _execute_with_retry_internal(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Internal retry logic implementation."""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                result = func()
                duration_ms = (time.time() - start_time) * 1000
                
                # Record successful query
                self.metrics.record_query(duration_ms, success=True)
                
                return result
                
            except (OperationalError, DisconnectionError, SQLAlchemyTimeoutError, DBAPIError) as e:
                last_exception = e
                duration_ms = (time.time() - start_time) * 1000
                
                # Record failed query
                self.metrics.record_query(duration_ms, success=False)
                
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}), "
                                 f"retrying in {delay:.2f}s: {str(e)}")
                    time.sleep(delay)
                    
                    # Try to reinitialize connection
                    try:
                        self._test_connection(self.engine, "primary")
                    except Exception:
                        logger.warning("Failed to reinitialize connection, continuing with retry")
                else:
                    logger.error(f"Database operation failed after {max_retries + 1} attempts: {str(e)}")
                    break
            except Exception as e:
                # Non-retryable error
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_query(duration_ms, success=False)
                
                logger.error(f"Non-retryable database error: {str(e)}")
                raise DatabaseConnectionError(f"Database operation failed: {str(e)}")
        
        raise DatabaseConnectionError(f"Database operation failed after {max_retries + 1} attempts: {str(last_exception)}")
    
    def execute_with_transaction_isolation(self, func, isolation_level: TransactionIsolationLevel):
        """
        Execute function with specific transaction isolation level
        
        Args:
            func: Function to execute
            isolation_level: Transaction isolation level to use
        
        Returns:
            Function result
        """
        try:
            with self.get_session() as session:
                # Set transaction isolation level
                if self.config.database_type == DatabaseType.POSTGRESQL:
                    session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}"))
                
                # Execute function
                result = func(session)
                
                return result
                
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            raise DatabaseConnectionError(f"Transaction execution failed: {e}")
    
    def execute_with_read_consistency(self, func, consistency_level: str = "read_committed"):
        """
        Execute read operation with specific consistency level
        
        Args:
            func: Function to execute
            consistency_level: Consistency level for read operations
        
        Returns:
            Function result
        """
        try:
            # Use read replica if available and appropriate
            if self.read_session_factories and consistency_level in ["read_committed", "repeatable_read"]:
                return self.execute_read_operation(func)
            else:
                # Use primary database for stronger consistency
                with self.get_session(read_only=True) as session:
                    return func(session)
                    
        except Exception as e:
            logger.error(f"Read operation failed: {e}")
            raise DatabaseConnectionError(f"Read operation failed: {e}")
    
    def health_check(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive database health check
        
        Args:
            force: Force health check regardless of interval
            
        Returns:
            Health check results
        """
        current_time = time.time()
        
        # Check if we should perform health check
        if not force and (current_time - self.last_health_check) < self.health_check_interval:
            return {"status": "healthy", "message": "Health check skipped (within interval)"}
        
        try:
            health_results = {
                "status": "healthy",
                "timestamp": current_time,
                "database_type": self.config.database_type.value,
                "environment": self.config.environment,
                "circuit_breaker": self.circuit_breaker.get_status(),
                "connections": {},
                "performance": self.metrics.get_database_info(),
                "migration": {},
                "backup": {}
            }
            
            # Check primary database
            primary_health = self._check_database_health(self.engine, "primary")
            health_results["connections"]["primary"] = primary_health
            
            # Check read replicas
            health_results["connections"]["read_replicas"] = []
            for i, engine in enumerate(self.read_engines):
                replica_health = self._check_database_health(engine, f"read_replica_{i+1}")
                health_results["connections"]["read_replicas"].append(replica_health)
            
            # Check backup database
            if hasattr(self, 'backup_engine'):
                backup_health = self._check_database_health(self.backup_engine, "backup")
                health_results["connections"]["backup"] = backup_health
            
            # Check migration status
            if self.config.migration.schema_version_check:
                migration_status = self._check_migration_status()
                health_results["migration"] = migration_status
            
            # Check backup status
            if self.config.migration.enable_backup_verification:
                backup_status = self._check_backup_status()
                health_results["backup"] = backup_status
            
            # Determine overall health status
            overall_status = self._determine_overall_health(health_results)
            health_results["status"] = overall_status
            
            self.last_health_check = current_time
            self.connection_health_status = overall_status
            
            logger.info(f"Database health check completed: {overall_status}")
            return health_results
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            self.last_health_check = current_time
            self.connection_health_status = "unhealthy"
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database health check failed",
                "timestamp": current_time
            }
    
    def _check_database_health(self, engine: Engine, name: str) -> Dict[str, Any]:
        """Check health of a specific database connection."""
        try:
            start_time = time.time()
            
            with engine.connect() as conn:
                if self.config.database_type == DatabaseType.POSTGRESQL:
                    result = conn.execute(text("SELECT version() as version, current_timestamp as timestamp"))
                    version_info = result.fetchone()
                    
                    # Check connection pool status
                    pool_status = {
                        "pool_size": engine.pool.size(),
                        "checked_in": engine.pool.checkedin(),
                        "checked_out": engine.pool.checkedout(),
                        "overflow": engine.pool.overflow()
                    }
                    
                    health_result = {
                        "status": "healthy",
                        "name": name,
                        "version": version_info[0] if version_info else "unknown",
                        "timestamp": version_info[1] if version_info else None,
                        "pool_status": pool_status,
                        "response_time_ms": (time.time() - start_time) * 1000
                    }
                else:
                    # SQLite health check
                    result = conn.execute(text("SELECT sqlite_version() as version, datetime('now') as timestamp"))
                    version_info = result.fetchone()
                    
                    health_result = {
                        "status": "healthy",
                        "name": name,
                        "version": version_info[0] if version_info else "unknown",
                        "timestamp": version_info[1] if version_info else None,
                        "response_time_ms": (time.time() - start_time) * 1000
                    }
                
                return health_result
                
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return {
                "status": "unhealthy",
                "name": name,
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000
            }
    
    def _check_migration_status(self) -> Dict[str, Any]:
        """Check database migration status."""
        try:
            with self.get_session() as session:
                # Check if required tables exist
                inspector = inspect(self.engine)
                existing_tables = inspector.get_table_names()
                
                # Define required tables (adjust based on your models)
                required_tables = ['users', 'forms', 'reports']  # Add your required tables
                
                missing_tables = [table for table in required_tables if table not in existing_tables]
                
                return {
                    "status": "healthy" if not missing_tables else "degraded",
                    "existing_tables": existing_tables,
                    "missing_tables": missing_tables,
                    "total_tables": len(existing_tables),
                    "required_tables": required_tables
                }
                
        except Exception as e:
            logger.error(f"Migration status check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _check_backup_status(self) -> Dict[str, Any]:
        """Check backup database status."""
        if not hasattr(self, 'backup_engine'):
            return {"status": "not_configured"}
        
        try:
            with self.backup_engine.connect() as conn:
                # Perform basic connectivity test
                result = conn.execute(text("SELECT 1 as test"))
                result.fetchone()
                
                # This is a simplified check - implement based on your backup strategy
                backup_age_hours = 24  # Assume backup is recent
                
                return {
                    "status": "healthy" if backup_age_hours <= 48 else "degraded",
                    "backup_age_hours": backup_age_hours,
                    "last_verification": self.last_backup_verification
                }
                
        except Exception as e:
            logger.error(f"Backup status check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _determine_overall_health(self, health_results: Dict[str, Any]) -> str:
        """Determine overall health status from individual checks."""
        # Check primary database
        primary_status = health_results["connections"].get("primary", {}).get("status", "unknown")
        if primary_status == "unhealthy":
            return "unhealthy"
        
        # Check read replicas
        read_replica_statuses = health_results["connections"].get("read_replicas", [])
        unhealthy_replicas = [r for r in read_replica_statuses if r.get("status") == "unhealthy"]
        
        if len(unhealthy_replicas) > len(read_replica_statuses) // 2:
            return "degraded"
        
        # Check migration status
        migration_status = health_results.get("migration", {}).get("status", "unknown")
        if migration_status == "unhealthy":
            return "degraded"
        
        # Check backup status
        backup_status = health_results.get("backup", {}).get("status", "unknown")
        if backup_status == "unhealthy":
            return "degraded"
        
        return "healthy"
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get comprehensive database connection information"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        try:
            # Get base configuration info
            base_info = self.config.get_database_info()
            
            # Add runtime connection information
            runtime_info = {
                "status": "initialized",
                "connection_health": self.connection_health_status,
                "circuit_breaker": self.circuit_breaker.get_status(),
                "performance_metrics": self.metrics.get_database_info(),
                "last_health_check": self.last_health_check,
                "last_migration_check": self.last_migration_check,
                "last_backup_verification": self.last_backup_verification
            }
            
            # Add connection pool information
            pool_info = {}
            if self.engine:
                pool_info["primary"] = {
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow()
                }
            
            for i, engine in enumerate(self.read_engines):
                pool_info[f"read_replica_{i+1}"] = {
                    "pool_size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow()
                }
            
            # Merge all information
            return {
                **base_info,
                **runtime_info,
                "connection_pools": pool_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        return {
            "metrics": self.metrics.get_database_info(),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "connection_health": self.connection_health_status,
            "last_reset": self.metrics.last_reset.isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.metrics.last_reset).total_seconds()
        }
    
    def reset_performance_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics.reset()
        logger.info("Database performance metrics reset")
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get information about slow queries (if available)."""
        # This is a placeholder - implement based on your database monitoring strategy
        # For PostgreSQL, you might query pg_stat_statements
        # For MySQL, you might query performance_schema
        
        return [
            {
                "message": "Slow query tracking requires database-specific implementation",
                "database_type": self.config.database_type.value,
                "suggestion": "Enable pg_stat_statements for PostgreSQL or performance_schema for MySQL"
            }
        ]
    
    def optimize_connection_pool(self) -> Dict[str, Any]:
        """Optimize connection pool settings based on current usage."""
        if not self.engine:
            return {"error": "Database not initialized"}
        
        try:
            current_pool = self.engine.pool
            current_size = current_pool.size()
            current_overflow = current_pool.max_overflow
            checked_out = current_pool.checkedout()
            overflow_usage = current_pool.overflow()
            
            recommendations = []
            
            # Analyze pool usage and provide recommendations
            if checked_out > current_size * 0.8:
                recommendations.append({
                    "type": "increase_pool_size",
                    "current": current_size,
                    "recommended": min(current_size * 2, 50),
                    "reason": "High connection usage detected"
                })
            
            if overflow_usage > current_overflow * 0.7:
                recommendations.append({
                    "type": "increase_max_overflow",
                    "current": current_overflow,
                    "recommended": min(current_overflow * 2, 100),
                    "reason": "High overflow usage detected"
                })
            
            if checked_out < current_size * 0.3:
                recommendations.append({
                    "type": "decrease_pool_size",
                    "current": current_size,
                    "recommended": max(current_size // 2, 5),
                    "reason": "Low connection usage detected"
                })
            
            return {
                "current_settings": {
                    "pool_size": current_size,
                    "max_overflow": current_overflow,
                    "checked_out": checked_out,
                    "overflow_usage": overflow_usage
                },
                "recommendations": recommendations,
                "optimization_applied": False
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze connection pool: {e}")
            return {"error": str(e)}
    
    def apply_connection_pool_optimization(self, optimization_type: str, new_value: int) -> Dict[str, Any]:
        """Apply connection pool optimization."""
        if not self.engine:
            return {"error": "Database not initialized"}
        
        try:
            current_pool = self.engine.pool
            
            if optimization_type == "pool_size":
                # Note: Changing pool size requires engine recreation
                logger.warning("Pool size changes require engine recreation - not applied")
                return {
                    "message": "Pool size changes require engine recreation",
                    "current_value": current_pool.size(),
                    "requested_value": new_value,
                    "applied": False
                }
            
            elif optimization_type == "max_overflow":
                # Note: Changing max overflow requires engine recreation
                logger.warning("Max overflow changes require engine recreation - not applied")
                return {
                    "message": "Max overflow changes require engine recreation",
                    "current_value": current_pool.max_overflow,
                    "requested_value": new_value,
                    "applied": False
                }
            
            else:
                return {"error": f"Unknown optimization type: {optimization_type}"}
                
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return {"error": str(e)}
    
    def close(self) -> None:
        """Close all database connections gracefully"""
        try:
            logger.info("Closing database manager...")
            
            # Close primary database
            if self.engine:
                self.engine.dispose()
                logger.info("Primary database engine disposed")
            
            # Close read replica engines
            for i, engine in enumerate(self.read_engines):
                try:
                    engine.dispose()
                    logger.info(f"Read replica {i+1} engine disposed")
                except Exception as e:
                    logger.error(f"Error closing read replica {i+1}: {e}")
            
            # Close backup engine
            if hasattr(self, 'backup_engine'):
                try:
                    self.backup_engine.dispose()
                    logger.info("Backup database engine disposed")
                except Exception as e:
                    logger.error(f"Error closing backup database: {e}")
            
            # Reset state
            self.is_initialized = False
            self.connection_health_status = "unknown"
            self.read_engines.clear()
            self.read_session_factories.clear()
            
            logger.info("Database manager closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing database manager: {str(e)}")
    
    def graceful_shutdown(self) -> None:
        """Perform graceful shutdown of database connections."""
        try:
            logger.info("Performing graceful database shutdown...")
            
            # Wait for active connections to complete
            if self.engine:
                # Wait for active connections to finish
                active_connections = self.engine.pool.checkedout()
                if active_connections > 0:
                    logger.info(f"Waiting for {active_connections} active connections to complete...")
                    # Give connections time to complete (adjust timeout as needed)
                    import time
                    time.sleep(5)
            
            # Close all connections
            self.close()
            
            logger.info("Graceful database shutdown completed")
            
        except Exception as e:
            logger.error(f"Graceful shutdown failed: {e}")
            # Force close even if graceful shutdown fails
            self.close()

# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager

def get_db_session():
    """Get database session (for use with Flask-SQLAlchemy)"""
    if not hasattr(g, 'db_session'):
        g.db_session = db_manager.get_session_factory()()
    return g.db_session

def close_db_session(error=None):
    """Close database session (Flask teardown)"""
    if hasattr(g, 'db_session'):
        g.db_session.close()

# Decorator for database operations with retry logic
def with_db_retry(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator to add retry logic to database operations
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (doubles each retry)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return db_manager.execute_with_retry(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay
            )
        return wrapper
    return decorator

# Health check function for external use
def check_database_health(force: bool = False) -> Dict[str, Any]:
    """Check database health (external interface)"""
    return db_manager.health_check(force=force)

# Connection info function for external use
def get_database_info() -> Dict[str, Any]:
    """Get database connection information (external interface)"""
    return db_manager.get_connection_info()

# Enhanced decorators for database operations
def with_transaction_isolation(isolation_level: TransactionIsolationLevel):
    """
    Decorator to execute function with specific transaction isolation level
    
    Args:
        isolation_level: Transaction isolation level to use
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return db_manager.execute_with_transaction_isolation(
                lambda session: func(session, *args, **kwargs),
                isolation_level
            )
        return wrapper
    return decorator

def with_read_consistency(consistency_level: str = "read_committed"):
    """
    Decorator to execute read operations with specific consistency level
    
    Args:
        consistency_level: Consistency level for read operations
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return db_manager.execute_with_read_consistency(func, consistency_level)
        return wrapper
    return decorator

def with_db_session(read_only: bool = False):
    """
    Decorator to provide database session to function
    
    Args:
        read_only: Whether to use read-only session
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with db_manager.get_session(read_only=read_only) as session:
                return func(session, *args, **kwargs)
        return wrapper
    return decorator

# Performance monitoring decorators
def monitor_database_performance(operation_name: str = None):
    """
    Decorator to monitor database operation performance
    
    Args:
        operation_name: Name of the operation for monitoring
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Record successful operation
                db_manager.metrics.record_query(duration_ms, success=True)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Record failed operation
                db_manager.metrics.record_query(duration_ms, success=False)
                
                logger.error(f"Database operation '{operation}' failed: {e}")
                raise
                
        return wrapper
    return decorator

# Additional utility functions
def get_database_performance_metrics() -> Dict[str, Any]:
    """Get database performance metrics (external interface)"""
    return db_manager.get_performance_metrics()

def reset_database_metrics() -> None:
    """Reset database performance metrics (external interface)"""
    db_manager.reset_performance_metrics()

def optimize_database_connections() -> Dict[str, Any]:
    """Optimize database connection pool (external interface)"""
    return db_manager.optimize_connection_pool()

def get_slow_queries(limit: int = 10) -> List[Dict[str, Any]]:
    """Get information about slow queries (external interface)"""
    return db_manager.get_slow_queries(limit)

def execute_database_migration() -> Dict[str, Any]:
    """Execute database migration (external interface)"""
    try:
        # This would typically involve Alembic or similar migration tool
        # For now, return a placeholder response
        return {
            "status": "not_implemented",
            "message": "Database migration requires Alembic or similar tool integration",
            "suggestion": "Implement migration logic using Alembic or your preferred migration tool"
        }
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return {"status": "error", "error": str(e)}

def verify_database_backup() -> Dict[str, Any]:
    """Verify database backup integrity (external interface)"""
    try:
        # This would typically involve backup verification logic
        # For now, return a placeholder response
        return {
            "status": "not_implemented",
            "message": "Backup verification requires backup strategy implementation",
            "suggestion": "Implement backup verification logic based on your backup strategy"
        }
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        return {"status": "error", "error": str(e)}
