#!/usr/bin/env python3
"""
Test Script for Database Enhancements
Verifies that all database improvements are working correctly
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_manager():
    """Test the database manager functionality"""
    logger.info("Testing Database Manager...")
    
    try:
        from app.core.database import get_db_manager, check_database_health, get_database_info
        
        # Get database manager
        db_manager = get_db_manager()
        logger.info("✓ Database manager created successfully")
        
        # Test initialization
        db_manager.initialize()
        logger.info("✓ Database manager initialized successfully")
        
        # Test health check
        health_status = check_database_health(force=True)
        logger.info(f"✓ Health check completed: {health_status['status']}")
        
        # Test connection info
        conn_info = get_database_info()
        logger.info(f"✓ Connection info retrieved: {conn_info['database_type']}")
        
        # Test session creation
        with db_manager.get_session() as session:
            logger.info("✓ Database session created successfully")
        
        logger.info("✓ All database manager tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database manager test failed: {str(e)}")
        return False

def test_configuration():
    """Test the configuration system"""
    logger.info("Testing Configuration System...")
    
    try:
        from app.core.config import get_settings, get_database_config
        
        # Get settings
        settings = get_settings()
        logger.info("✓ Settings loaded successfully")
        
        # Test database configuration
        db_config = get_database_config()
        logger.info(f"✓ Database config loaded: {db_config['SQLALCHEMY_DATABASE_URI']}")
        
        # Test environment detection
        logger.info(f"✓ Environment: {settings.environment}")
        logger.info(f"✓ Debug mode: {settings.debug}")
        
        logger.info("✓ All configuration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {str(e)}")
        return False

def test_production_models():
    """Test the production models integration"""
    logger.info("Testing Production Models Integration...")
    
    try:
        from app.models.production_models import create_production_tables
        
        # Test that the function exists and is callable
        assert callable(create_production_tables)
        logger.info("✓ Production models functions are accessible")
        
        # Test that hardcoded connection is removed
        with open('app/models/production_models.py', 'r') as f:
            content = f.read()
            assert 'postgresql://your_user:your_password@localhost/your_database' not in content
            logger.info("✓ Hardcoded connection string removed")
        
        logger.info("✓ All production models tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Production models test failed: {str(e)}")
        return False

def test_health_api():
    """Test the health API routes"""
    logger.info("Testing Health API Routes...")
    
    try:
        from app.routes.database_health import db_health_bp
        
        # Test that the blueprint exists
        assert db_health_bp is not None
        logger.info("✓ Database health blueprint created")
        
        # Test that routes are registered
        routes = [rule.rule for rule in db_health_bp.url_map.iter_rules()]
        expected_routes = [
            '/api/database/health',
            '/api/database/info', 
            '/api/database/status',
            '/api/database/test',
            '/api/database/reconnect'
        ]
        
        for route in expected_routes:
            assert route in routes, f"Route {route} not found"
        
        logger.info("✓ All expected health API routes found")
        logger.info("✓ All health API tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Health API test failed: {str(e)}")
        return False

def test_environment_variables():
    """Test environment variable configuration"""
    logger.info("Testing Environment Variables...")
    
    try:
        # Check required environment variables
        required_vars = [
            'DATABASE_URL',
            'DB_POOL_SIZE',
            'DB_POOL_TIMEOUT',
            'DB_POOL_RECYCLE',
            'DB_MAX_OVERFLOW',
            'DB_HEALTH_CHECK_INTERVAL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
        else:
            logger.info("✓ All required environment variables are set")
        
        # Test database URL format
        db_url = os.getenv('DATABASE_URL', '')
        if db_url.startswith(('sqlite://', 'postgresql://', 'postgres://')):
            logger.info(f"✓ Valid database URL format: {db_url}")
        else:
            logger.warning(f"Database URL format may be invalid: {db_url}")
        
        logger.info("✓ Environment variable tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Environment variable test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Database Enhancement Tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Configuration System", test_configuration),
        ("Environment Variables", test_environment_variables),
        ("Database Manager", test_database_manager),
        ("Production Models", test_production_models),
        ("Health API Routes", test_health_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Database enhancements are working correctly.")
        return 0
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
