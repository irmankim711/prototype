#!/usr/bin/env python3
"""
Test Environment Variable Loading
Verifies that the enhanced environment loader is working correctly
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def test_environment_loading():
    """Test the environment loading system"""
    print("🧪 Testing Environment Variable Loading...")
    print("=" * 50)
    
    # Test 1: Check if environment loader can be imported
    try:
        from app.core.env_loader import load_environment, get_environment_info, force_development_mode
        print("✅ Environment loader imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import environment loader: {e}")
        return False
    
    # Test 2: Check current environment before loading
    print(f"\n🔍 Environment before loading:")
    print(f"   FLASK_ENV: {os.getenv('FLASK_ENV', 'NOT_SET')}")
    print(f"   DEBUG: {os.getenv('DEBUG', 'NOT_SET')}")
    print(f"   TESTING: {os.getenv('TESTING', 'NOT_SET')}")
    
    # Test 3: Load environment
    print(f"\n📁 Loading environment variables...")
    success = load_environment()
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 4: Check environment after loading
    print(f"\n🔍 Environment after loading:")
    print(f"   FLASK_ENV: {os.getenv('FLASK_ENV', 'NOT_SET')}")
    print(f"   DEBUG: {os.getenv('DEBUG', 'NOT_SET')}")
    print(f"   TESTING: {os.getenv('TESTING', 'NOT_SET')}")
    
    # Test 5: Get detailed environment info
    env_info = get_environment_info()
    print(f"\n📊 Environment Information:")
    print(f"   Current Environment: {env_info['current_environment']}")
    print(f"   Debug Mode: {env_info['debug_mode']}")
    print(f"   Files Loaded: {len(env_info['loaded_files'])}")
    print(f"   Overridden Variables: {len(env_info['overridden_variables'])}")
    print(f"   Missing Variables: {len(env_info['missing_variables'])}")
    
    if env_info['loaded_files']:
        print(f"   Loaded Files:")
        for file in env_info['loaded_files']:
            print(f"      - {file}")
    
    if env_info['overridden_variables']:
        print(f"   Overridden Variables:")
        for var in env_info['overridden_variables']:
            print(f"      - {var['key']} (from {var['file']}:{var['line']})")
    
    if env_info['missing_variables']:
        print(f"   Missing Variables:")
        for var in env_info['missing_variables']:
            print(f"      - {var}")
    
    # Test 6: Test force development mode
    print(f"\n🔧 Testing force development mode...")
    force_development_mode()
    print(f"   FLASK_ENV after force: {os.getenv('FLASK_ENV', 'NOT_SET')}")
    print(f"   DEBUG after force: {os.getenv('DEBUG', 'NOT_SET')}")
    
    # Test 7: Check critical environment variables
    print(f"\n🔑 Critical Environment Variables:")
    critical_vars = [
        'FLASK_ENV',
        'SECRET_KEY', 
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'CELERY_BROKER_URL'
    ]
    
    for var in critical_vars:
        value = os.getenv(var, 'NOT_SET')
        status = "✅" if value != 'NOT_SET' else "❌"
        print(f"   {status} {var}: {value}")
    
    # Test 8: Check if configuration can be loaded
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"\n✅ Configuration loaded successfully:")
        print(f"   Environment: {settings.environment}")
        print(f"   Debug: {settings.debug}")
        print(f"   Testing: {settings.testing}")
    except Exception as e:
        print(f"\n❌ Failed to load configuration: {e}")
        return False
    
    print(f"\n🎉 Environment loading test completed!")
    return True

def test_app_creation():
    """Test if the Flask app can be created with the new environment loading"""
    print(f"\n🚀 Testing Flask App Creation...")
    print("=" * 50)
    
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        
        # Check app configuration
        print(f"   App ENV: {app.config.get('ENV')}")
        print(f"   App DEBUG: {app.config.get('DEBUG')}")
        print(f"   App TESTING: {app.config.get('TESTING')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create Flask app: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🧪 Environment Loading Test Suite")
    print("=" * 60)
    
    # Run tests
    env_test = test_environment_loading()
    app_test = test_app_creation()
    
    print(f"\n📊 Test Results:")
    print(f"   Environment Loading: {'✅ PASS' if env_test else '❌ FAIL'}")
    print(f"   Flask App Creation: {'✅ PASS' if app_test else '❌ FAIL'}")
    
    if env_test and app_test:
        print(f"\n🎉 All tests passed! Environment loading is working correctly.")
        sys.exit(0)
    else:
        print(f"\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
