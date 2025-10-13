#!/usr/bin/env python3
"""
Test script to verify error handling and visibility
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def test_import_error():
    """Test that import errors are visible"""
    print("🔍 Testing import error handling...")
    try:
        # This should trigger an import if there are issues
        from app import create_app
        print("✅ App import successful")
        
        app = create_app()
        print("✅ App creation successful")
        
        # Test basic route
        with app.test_client() as client:
            response = client.get('/health')
            print(f"🏥 Health check: {response.status_code}")
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Application Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        from app import create_app, db
        from app.models import User
        
        app = create_app()
        with app.app_context():
            # Try to query users
            users = User.query.all()
            print(f"📊 Found {len(users)} users in database")
            
    except Exception as e:
        print(f"❌ Database Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("🧪 Running error handling tests...")
    print("=" * 50)
    
    success = True
    
    # Test 1: Import and app creation
    if not test_import_error():
        success = False
    
    print("-" * 30)
    
    # Test 2: Database connection
    if not test_database_connection():
        success = False
    
    print("=" * 50)
    if success:
        print("✅ All tests passed - your app should run without hidden errors")
    else:
        print("❌ Some tests failed - check the errors above")
    
    print("💡 Now try running: python run.py")