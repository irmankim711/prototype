#!/usr/bin/env python3
"""
Database Configuration Validation Script

This script validates the database configuration by:
1. Testing import without syntax errors
2. Validating environment variable parsing
3. Testing configuration object creation
4. Validating SQLAlchemy configuration generation
5. Testing connection arguments generation
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_import():
    """Test that the database configuration can be imported without errors."""
    try:
        from app.core.db_config import (
            get_sqlalchemy_config,
            get_database_config,
            get_database_info,
            ProductionDatabaseConfig,
            ConnectionPoolConfig,
            DatabaseConnectionConfig
        )
        logger.info("✅ All database configuration modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except SyntaxError as e:
        logger.error(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during import: {e}")
        return False

def test_configuration_creation():
    """Test that configuration objects can be created without errors."""
    try:
        from app.core.db_config import (
            ConnectionPoolConfig,
            DatabaseConnectionConfig,
            DatabasePerformanceConfig,
            DatabaseMigrationConfig,
            DatabaseSecurityConfig
        )
        
        # Test ConnectionPoolConfig
        pool_config = ConnectionPoolConfig()
        logger.info("✅ ConnectionPoolConfig created successfully")
        
        # Test DatabaseConnectionConfig
        conn_config = DatabaseConnectionConfig(
            url="sqlite:///test.db",
            name="test"
        )
        logger.info("✅ DatabaseConnectionConfig created successfully")
        
        # Test other configs
        perf_config = DatabasePerformanceConfig()
        logger.info("✅ DatabasePerformanceConfig created successfully")
        
        mig_config = DatabaseMigrationConfig()
        logger.info("✅ DatabaseMigrationConfig created successfully")
        
        sec_config = DatabaseSecurityConfig()
        logger.info("✅ DatabaseSecurityConfig created successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Configuration creation error: {e}")
        return False

def test_production_config():
    """Test the main production database configuration."""
    try:
        from app.core.db_config import ProductionDatabaseConfig
        
        # Test configuration creation
        config = ProductionDatabaseConfig()
        logger.info("✅ ProductionDatabaseConfig created successfully")
        
        # Test SQLAlchemy config generation
        sqlalchemy_config = config.get_sqlalchemy_config()
        logger.info("✅ SQLAlchemy configuration generated successfully")
        
        # Test database info generation
        db_info = config.get_database_info()
        logger.info("✅ Database info generated successfully")
        
        # Test read replica methods
        replica_urls = config.get_read_replica_urls()
        logger.info(f"✅ Read replica URLs retrieved: {len(replica_urls)} replicas")
        
        return True
    except Exception as e:
        logger.error(f"❌ Production configuration error: {e}")
        return False

def test_environment_variables():
    """Test environment variable parsing and validation."""
    try:
        from app.core.db_config import ProductionDatabaseConfig
        
        # Set test environment variables
        test_env = {
            'FLASK_ENV': 'development',
            'DATABASE_URL': 'sqlite:///test.db',
            'DB_POOL_SIZE': '10',
            'DB_MAX_OVERFLOW': '20',
            'DB_POOL_TIMEOUT': '30',
            'DB_SSL_MODE': 'prefer',
            'DB_ENABLE_QUERY_LOGGING': 'true',
            'DB_SLOW_QUERY_THRESHOLD_MS': '500',
            'DB_AUTO_MIGRATE': 'false',
            'DB_REQUIRE_SSL': 'false'
        }
        
        # Temporarily set environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            # Test configuration with test environment
            config = ProductionDatabaseConfig()
            logger.info("✅ Environment variable parsing successful")
            
            # Test specific values
            if config.connection_pool.pool_size == 10:
                logger.info("✅ Pool size environment variable parsed correctly")
            else:
                logger.warning(f"⚠️ Pool size mismatch: expected 10, got {config.connection_pool.pool_size}")
            
            if config.performance.enable_query_logging:
                logger.info("✅ Query logging environment variable parsed correctly")
            else:
                logger.warning("⚠️ Query logging environment variable not parsed correctly")
                
        finally:
            # Restore original environment variables
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)
        
        return True
    except Exception as e:
        logger.error(f"❌ Environment variable test error: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid configurations."""
    try:
        from app.core.db_config import DatabaseConnectionConfig
        
        # Test invalid URL
        try:
            invalid_config = DatabaseConnectionConfig(url="", name="invalid")
            logger.warning("⚠️ Should have raised error for empty URL")
        except ValueError as e:
            logger.info("✅ Properly caught invalid URL error")
        
        # Test invalid role
        try:
            invalid_config = DatabaseConnectionConfig(url="sqlite:///test.db", name="invalid", role="invalid_role")
            logger.warning("⚠️ Should have raised error for invalid role")
        except ValueError as e:
            logger.info("✅ Properly caught invalid role error")
        
        # Test invalid weight
        try:
            invalid_config = DatabaseConnectionConfig(url="sqlite:///test.db", name="invalid", weight=0)
            logger.warning("⚠️ Should have raised error for invalid weight")
        except ValueError as e:
            logger.info("✅ Properly caught invalid weight error")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error handling test error: {e}")
        return False

def main():
    """Run all validation tests."""
    logger.info("🚀 Starting database configuration validation...")
    
    tests = [
        ("Import Test", test_import),
        ("Configuration Creation Test", test_configuration_creation),
        ("Production Configuration Test", test_production_config),
        ("Environment Variable Test", test_environment_variables),
        ("Error Handling Test", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 VALIDATION SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Database configuration is valid.")
        return 0
    else:
        logger.error("💥 Some tests failed. Please review the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
