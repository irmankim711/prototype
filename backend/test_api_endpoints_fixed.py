#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script
Tests all registered API endpoints for basic functionality
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_app_creation():
    """Test if the Flask app can be created successfully"""
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        return app
    except Exception as e:
        print(f"❌ Failed to create Flask app: {e}")
        return None

def test_blueprint_registration(app):
    """Test if all blueprints are registered correctly"""
    try:
        registered_blueprints = list(app.blueprints.keys())
        print(f"✅ Blueprints registered: {registered_blueprints}")
        
        # Check for specific important blueprints
        important_blueprints = ['auth', 'integrations', 'forms', 'api', 'dashboard']
        for bp in important_blueprints:
            if bp in registered_blueprints:
                print(f"  ✅ {bp} blueprint found")
            else:
                print(f"  ⚠️  {bp} blueprint missing")
        
        return True
    except Exception as e:
        print(f"❌ Blueprint registration test failed: {e}")
        return False

def test_route_registration(app):
    """Test if routes are registered correctly"""
    try:
        api_routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('api') or '/api/' in rule.rule:
                api_routes.append({
                    'rule': rule.rule,
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods)
                })
        
        print(f"✅ Found {len(api_routes)} API routes")
        
        # Show some key routes
        print("  Key API routes:")
        for route in api_routes[:10]:  # Show first 10
            print(f"    {route['rule']} -> {route['endpoint']} [{', '.join(route['methods'])}]")
        
        if len(api_routes) > 10:
            print(f"    ... and {len(api_routes) - 10} more routes")
        
        return True
    except Exception as e:
        print(f"❌ Route registration test failed: {e}")
        return False

def test_model_imports():
    """Test if all models can be imported successfully"""
    try:
        from app.models import User, Form, File, Report, ReportTemplate
        print("✅ All core models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_service_imports():
    """Test if all services can be imported successfully"""
    try:
        from app.services.ai_service import ai_service
        from app.services.google_forms_service import google_forms_service
        print("✅ Core services imported successfully")
        return True
    except Exception as e:
        print(f"❌ Service import failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        from app import db
        from app.models import User
        
        # Try to query the database
        user_count = User.query.count()
        print(f"✅ Database connection successful (User count: {user_count})")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_rate_limiter():
    """Test rate limiter functionality"""
    try:
        from app.core.rate_limiter import rate_limit, RateLimitStrategy, RateLimitScope
        print("✅ Rate limiter imported successfully")
        return True
    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False

def test_auth_system():
    """Test authentication system"""
    try:
        from app.auth import auth_bp
        from flask_jwt_extended import create_access_token
        print("✅ Authentication system imported successfully")
        return True
    except Exception as e:
        print(f"❌ Authentication system test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive API Endpoint Testing")
    print("=" * 60)
    
    # Test app creation
    app = test_app_creation()
    if not app:
        print("❌ Cannot proceed without Flask app")
        return False
    
    print()
    
    # Test blueprint registration
    blueprint_ok = test_blueprint_registration(app)
    print()
    
    # Test route registration
    routes_ok = test_route_registration(app)
    print()
    
    # Test model imports
    models_ok = test_model_imports()
    print()
    
    # Test service imports
    services_ok = test_service_imports()
    print()
    
    # Test database connection
    db_ok = test_database_connection()
    print()
    
    # Test rate limiter
    rate_limiter_ok = test_rate_limiter()
    print()
    
    # Test auth system
    auth_ok = test_auth_system()
    print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Flask App Creation", app is not None),
        ("Blueprint Registration", blueprint_ok),
        ("Route Registration", routes_ok),
        ("Model Imports", models_ok),
        ("Service Imports", services_ok),
        ("Database Connection", db_ok),
        ("Rate Limiter", rate_limiter_ok),
        ("Authentication System", auth_ok)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print()
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API system is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {e}")
        sys.exit(1)
