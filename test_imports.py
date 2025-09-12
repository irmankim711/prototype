#!/usr/bin/env python3
"""
Test script to check if all required imports are working
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test importing all required modules"""
    print("🔍 Testing imports...")
    
    try:
        print("📦 Testing Flask imports...")
        from flask import Flask, Blueprint, request, jsonify, current_app
        print("✅ Flask imports successful")
    except Exception as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        print("📦 Testing database imports...")
        from app import db
        print("✅ Database import successful")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        print("📦 Testing model imports...")
        from app.models import Report, ReportTemplate, User
        print("✅ Model imports successful")
    except Exception as e:
        print(f"❌ Model imports failed: {e}")
        return False
    
    try:
        print("📦 Testing decorator imports...")
        from app.decorators import get_current_user_id
        print("✅ Decorator imports successful")
    except Exception as e:
        print(f"❌ Decorator import failed: {e}")
        return False
    
    try:
        print("📦 Testing API routes...")
        from app.routes.api import api
        print("✅ API routes import successful")
    except Exception as e:
        print(f"❌ API routes import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test if database connection works"""
    try:
        print("\n🔍 Testing database connection...")
        
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Try to query the database
            from app.models import User
            user_count = User.query.count()
            print(f"✅ Database connection successful - Found {user_count} users")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Import and Database Test")
    print("=" * 50)
    
    imports_ok = test_imports()
    
    if imports_ok:
        test_database_connection()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed")
