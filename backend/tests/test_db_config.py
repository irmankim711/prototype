"""
Unit tests for database configuration module.

These tests ensure:
1. No syntax errors in the configuration
2. Proper environment variable parsing
3. Correct dataclass field definitions
4. Validation logic works correctly
5. Error handling is robust
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the app directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from app.core.db_config import (
    ConnectionPoolConfig,
    DatabaseConnectionConfig,
    DatabasePerformanceConfig,
    DatabaseMigrationConfig,
    DatabaseSecurityConfig,
    ProductionDatabaseConfig,
    get_sqlalchemy_config,
    get_database_config,
    get_database_info,
    DatabaseType,
    TransactionIsolationLevel
)

class TestConnectionPoolConfig:
    """Test ConnectionPoolConfig dataclass."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = ConnectionPoolConfig()
        
        assert config.pool_size == 20
        assert config.max_overflow == 30
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.pool_pre_ping is True
        assert config.pool_reset_on_return == "commit"
        assert config.pool_use_lifo is False
        assert config.pool_validation_interval == 300
        assert config.pool_echo_pool is False
        assert config.pool_overflow_timeout == 60
        assert config.pool_overflow_shutdown is False
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'DB_POOL_SIZE': '50',
            'DB_MAX_OVERFLOW': '100',
            'DB_POOL_TIMEOUT': '60',
            'DB_POOL_PRE_PING': 'false'
        }):
            config = ConnectionPoolConfig()
            
            assert config.pool_size == 50
            assert config.max_overflow == 100
            assert config.pool_timeout == 60
            assert config.pool_pre_ping is False
    
    def test_invalid_environment_variables(self):
        """Test handling of invalid environment variable values."""
        with patch.dict(os.environ, {
            'DB_POOL_SIZE': 'invalid',
            'DB_MAX_OVERFLOW': 'not_a_number'
        }):
            # Should handle gracefully and use defaults
            config = ConnectionPoolConfig()
            assert config.pool_size == 20  # Default value
            assert config.max_overflow == 30  # Default value

class TestDatabaseConnectionConfig:
    """Test DatabaseConnectionConfig dataclass."""
    
    def test_required_fields(self):
        """Test that required fields are properly set."""
        config = DatabaseConnectionConfig(
            url="sqlite:///test.db",
            name="test_db"
        )
        
        assert config.url == "sqlite:///test.db"
        assert config.name == "test_db"
        assert config.role == "read_write"  # Default
        assert config.weight == 1  # Default
    
    def test_optional_fields(self):
        """Test that optional fields can be set."""
        config = DatabaseConnectionConfig(
            url="postgresql://localhost/test",
            name="postgres_db",
            role="read_only",
            weight=5
        )
        
        assert config.role == "read_only"
        assert config.weight == 5
    
    def test_environment_variable_parsing(self):
        """Test environment variable parsing for connection settings."""
        with patch.dict(os.environ, {
            'DB_CONNECT_TIMEOUT': '15',
            'DB_COMMAND_TIMEOUT': '45',
            'DB_APPLICATION_NAME': 'test_app',
            'DB_SSL_MODE': 'require',
            'DB_MAX_CONNECTIONS': '200',
            'DB_MIN_CONNECTIONS': '10'
        }):
            config = DatabaseConnectionConfig(
                url="postgresql://localhost/test",
                name="test_db"
            )
            
            assert config.connect_timeout == 15
            assert config.command_timeout == 45
            assert config.application_name == "test_app"
            assert config.ssl_mode == "require"
            assert config.max_connections == 200
            assert config.min_connections == 10
    
    def test_validation_errors(self):
        """Test that validation errors are raised for invalid values."""
        # Empty URL
        with pytest.raises(ValueError, match="Database URL is required"):
            DatabaseConnectionConfig(url="", name="test")
        
        # Invalid role
        with pytest.raises(ValueError, match="Invalid database role"):
            DatabaseConnectionConfig(
                url="sqlite:///test.db",
                name="test",
                role="invalid_role"
            )
        
        # Invalid weight
        with pytest.raises(ValueError, match="Database weight must be >= 1"):
            DatabaseConnectionConfig(
                url="sqlite:///test.db",
                name="test",
                weight=0
            )

class TestDatabaseSecurityConfig:
    """Test DatabaseSecurityConfig dataclass."""
    
    def test_default_values(self):
        """Test default security configuration values."""
        config = DatabaseSecurityConfig()
        
        assert config.require_ssl is True
        assert config.ssl_verify_mode == "required"
        assert config.connection_encryption is True
        assert config.password_encryption is True
        assert config.connection_limit_per_user == 10
        assert config.max_failed_connections == 3
    
    def test_environment_variable_override(self):
        """Test environment variable override for security settings."""
        with patch.dict(os.environ, {
            'DB_REQUIRE_SSL': 'false',
            'DB_SSL_VERIFY_MODE': 'optional',
            'DB_CONNECTION_ENCRYPTION': 'false',
            'DB_PASSWORD_ENCRYPTION': 'false',
            'DB_CONNECTION_LIMIT_PER_USER': '5',
            'DB_MAX_FAILED_CONNECTIONS': '5'
        }):
            config = DatabaseSecurityConfig()
            
            assert config.require_ssl is False
            assert config.ssl_verify_mode == "optional"
            assert config.connection_encryption is False
            assert config.password_encryption is False
            assert config.connection_limit_per_user == 5
            assert config.max_failed_connections == 5

class TestProductionDatabaseConfig:
    """Test ProductionDatabaseConfig class."""
    
    def test_initialization(self):
        """Test that the configuration initializes without errors."""
        with patch.dict(os.environ, {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///test.db'
        }):
            config = ProductionDatabaseConfig()
            
            assert config.environment == 'development'
            assert config.database_type == DatabaseType.SQLITE
            assert config.primary_database is not None
            assert config.connection_pool is not None
            assert config.performance is not None
            assert config.migration is not None
            assert config.security is not None
    
    def test_database_type_detection(self):
        """Test database type detection from URLs."""
        test_cases = [
            ('postgresql://localhost/test', DatabaseType.POSTGRESQL),
            ('postgres://localhost/test', DatabaseType.POSTGRESQL),
            ('mysql://localhost/test', DatabaseType.MYSQL),
            ('sqlite:///test.db', DatabaseType.SQLITE),
            ('unknown://localhost/test', DatabaseType.SQLITE)  # Default fallback
        ]
        
        for url, expected_type in test_cases:
            with patch.dict(os.environ, {'DATABASE_URL': url}):
                config = ProductionDatabaseConfig()
                assert config.database_type == expected_type
    
    def test_sqlalchemy_config_generation(self):
        """Test SQLAlchemy configuration generation."""
        with patch.dict(os.environ, {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///test.db'
        }):
            config = ProductionDatabaseConfig()
            sqlalchemy_config = config.get_sqlalchemy_config()
            
            assert 'SQLALCHEMY_DATABASE_URI' in sqlalchemy_config
            assert 'SQLALCHEMY_ENGINE_OPTIONS' in sqlalchemy_config
            assert sqlalchemy_config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///test.db'
            assert sqlalchemy_config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False
    
    def test_read_replica_configuration(self):
        """Test read replica configuration parsing."""
        with patch.dict(os.environ, {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///primary.db',
            'DB_READ_REPLICA_URLS': 'sqlite:///replica1.db,sqlite:///replica2.db',
            'DB_READ_REPLICA_1_WEIGHT': '3',
            'DB_READ_REPLICA_2_WEIGHT': '7'
        }):
            config = ProductionDatabaseConfig()
            
            assert len(config.read_replicas) == 2
            assert config.read_replicas[0].url == 'sqlite:///replica1.db'
            assert config.read_replicas[0].weight == 3
            assert config.read_replicas[1].url == 'sqlite:///replica2.db'
            assert config.read_replicas[1].weight == 7
    
    def test_validation_errors(self):
        """Test configuration validation."""
        # Missing primary database URL
        with patch.dict(os.environ, {'FLASK_ENV': 'development'}):
            with pytest.raises(ValueError, match="Primary database URL is required"):
                ProductionDatabaseConfig()
        
        # Invalid pool settings
        with patch.dict(os.environ, {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///test.db',
            'DB_POOL_SIZE': '0',
            'DB_MAX_OVERFLOW': '-1'
        }):
            with pytest.raises(ValueError, match="Connection pool size must be >= 1"):
                ProductionDatabaseConfig()

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_get_sqlalchemy_config(self):
        """Test get_sqlalchemy_config utility function."""
        with patch.dict(os.environ, {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///test.db'
        }):
            config = get_sqlalchemy_config()
            assert isinstance(config, dict)
            assert 'SQLALCHEMY_DATABASE_URI' in config
    
    def test_get_database_config(self):
        """Test get_database_config utility function."""
        with patch.dict(os.environ, {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///test.db'
        }):
            config = get_database_config()
            assert isinstance(config, ProductionDatabaseConfig)
    
    def test_get_database_info(self):
        """Test get_database_info utility function."""
        with patch.dict(os.environ, {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///test.db'
        }):
            info = get_database_info()
            assert isinstance(info, dict)
            assert 'database_type' in info
            assert 'environment' in info
            assert 'primary_database' in info

class TestEnums:
    """Test enum classes."""
    
    def test_database_type_enum(self):
        """Test DatabaseType enum values."""
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.SQLITE.value == "sqlite"
    
    def test_transaction_isolation_enum(self):
        """Test TransactionIsolationLevel enum values."""
        assert TransactionIsolationLevel.READ_UNCOMMITTED.value == "READ UNCOMMITTED"
        assert TransactionIsolationLevel.READ_COMMITTED.value == "READ COMMITTED"
        assert TransactionIsolationLevel.REPEATABLE_READ.value == "REPEATABLE READ"
        assert TransactionIsolationLevel.SERIALIZABLE.value == "SERIALIZABLE"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
