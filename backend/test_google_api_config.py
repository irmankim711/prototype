#!/usr/bin/env python3
"""
Test script to verify Google API configuration and dependencies.
This script tests the Google API setup for Forms and Sheets integration.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_google_api_imports():
    """Test that all required Google API packages can be imported."""
    print("Testing Google API package imports...")
    
    try:
        import google.auth
        print("✓ google.auth imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import google.auth: {e}")
        return False
    
    try:
        import google.auth.transport.requests
        print("✓ google.auth.transport.requests imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import google.auth.transport.requests: {e}")
        return False
    
    try:
        from google.auth.transport.requests import Request
        print("✓ google.auth.transport.requests.Request imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Request: {e}")
        return False
    
    try:
        from google_auth_oauthlib.flow import Flow
        print("✓ google_auth_oauthlib.flow.Flow imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Flow: {e}")
        return False
    
    try:
        from google_auth_httplib2 import Request as HttplibRequest
        print("✓ google_auth_httplib2.Request imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import HttplibRequest: {e}")
        return False
    
    try:
        from googleapiclient.discovery import build
        print("✓ googleapiclient.discovery.build imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import build: {e}")
        return False
    
    try:
        from googleapiclient.errors import HttpError
        print("✓ googleapiclient.errors.HttpError imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import HttpError: {e}")
        return False
    
    return True

def test_config_loading():
    """Test that configuration can be loaded properly."""
    print("\nTesting configuration loading...")
    
    try:
        from config import Config
        print("✓ Config class imported successfully")
        
        # Test Google API configuration attributes
        config_attrs = [
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET', 
            'GOOGLE_REDIRECT_URI',
            'GOOGLE_SCOPES',
            'GOOGLE_API_RATE_LIMIT',
            'GOOGLE_API_QUOTA_USER',
            'GOOGLE_API_MAX_RETRIES',
            'GOOGLE_API_RETRY_DELAY',
            'GOOGLE_API_BACKOFF_FACTOR',
            'GOOGLE_API_TIMEOUT',
            'GOOGLE_API_CONNECT_TIMEOUT'
        ]
        
        for attr in config_attrs:
            if hasattr(Config, attr):
                value = getattr(Config, attr)
                print(f"✓ {attr}: {value if attr not in ['GOOGLE_CLIENT_SECRET'] else '***HIDDEN***'}")
            else:
                print(f"✗ Missing configuration attribute: {attr}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import Config: {e}")
        return False
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        return False

def test_environment_variables():
    """Test that environment variables are properly set."""
    print("\nTesting environment variables...")
    
    env_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'GOOGLE_REDIRECT_URI',
        'GOOGLE_API_RATE_LIMIT',
        'GOOGLE_API_QUOTA_USER',
        'GOOGLE_API_MAX_RETRIES',
        'GOOGLE_API_RETRY_DELAY',
        'GOOGLE_API_BACKOFF_FACTOR',
        'GOOGLE_API_TIMEOUT',
        'GOOGLE_API_CONNECT_TIMEOUT'
    ]
    
    missing_vars = []
    for var in env_vars:
        value = os.getenv(var)
        if value:
            display_value = value if var != 'GOOGLE_CLIENT_SECRET' else '***HIDDEN***'
            print(f"✓ {var}: {display_value}")
        else:
            print(f"⚠ {var}: Not set (will use default if available)")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\nNote: {len(missing_vars)} environment variables are not set.")
        print("This is normal for development if using defaults from config.py")
    
    return True

def test_google_scopes():
    """Test that Google API scopes are properly configured."""
    print("\nTesting Google API scopes...")
    
    try:
        from config import Config
        scopes = Config.GOOGLE_SCOPES
        
        expected_scopes = [
            'https://www.googleapis.com/auth/forms.responses.readonly',
            'https://www.googleapis.com/auth/forms.body.readonly',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        print(f"Configured scopes: {len(scopes)}")
        for scope in scopes:
            print(f"  ✓ {scope}")
        
        missing_scopes = [scope for scope in expected_scopes if scope not in scopes]
        if missing_scopes:
            print(f"\n✗ Missing required scopes:")
            for scope in missing_scopes:
                print(f"  - {scope}")
            return False
        
        print("✓ All required scopes are configured")
        return True
        
    except Exception as e:
        print(f"✗ Error checking scopes: {e}")
        return False

def main():
    """Run all configuration tests."""
    print("Google API Configuration Test")
    print("=" * 50)
    
    tests = [
        ("Google API Package Imports", test_google_api_imports),
        ("Configuration Loading", test_config_loading),
        ("Environment Variables", test_environment_variables),
        ("Google API Scopes", test_google_scopes)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("✓ All tests passed! Google API configuration is ready.")
        return 0
    else:
        print("✗ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())