#!/usr/bin/env python3
"""
Test database connectivity with Flask app
"""
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_flask_db_connection():
    """Test if Flask app can connect to database"""
    
    print("=" * 50)
    print("TESTING FLASK DATABASE CONNECTIVITY")
    print("=" * 50)
    
    try:
        # Import Flask app components
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        # Create minimal Flask app
        app = Flask(__name__)
        
        # Configure database
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy
        db = SQLAlchemy()
        db.init_app(app)
        
        with app.app_context():
            print("✅ Flask app context created successfully")
            
            # Test database connection
            try:
                # Simple query to test connection
                result = db.session.execute(db.text("SELECT COUNT(*) FROM user"))
                count = result.scalar()
                print(f"✅ Database connection successful - User count: {count}")
                
                # Test table listing
                result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = result.fetchall()
                print(f"✅ Database tables accessible - Found {len(tables)} tables")
                
                return True
                
            except Exception as e:
                print(f"❌ Database query failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_endpoints():
    """Test if database endpoints are working"""
    
    print("\n" + "=" * 50)
    print("TESTING DATABASE ENDPOINTS")
    print("=" * 50)
    
    try:
        # Import the actual Flask app
        from app import create_app, db
        
        # Create app
        app = create_app()
        
        with app.app_context():
            print("✅ Production Flask app created successfully")
            
            # Test database connection
            try:
                # Test if we can access the database
                result = db.session.execute(db.text("SELECT COUNT(*) FROM user"))
                count = result.scalar()
                print(f"✅ Production app database connection successful - User count: {count}")
                
                return True
                
            except Exception as e:
                print(f"❌ Production app database query failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Production Flask app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing database connectivity...")
    
    # Test basic Flask + SQLAlchemy
    basic_test = test_flask_db_connection()
    
    # Test production Flask app
    production_test = test_database_endpoints()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Basic Flask + SQLAlchemy: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"Production Flask App: {'✅ PASS' if production_test else '❌ FAIL'}")
    
    if basic_test and production_test:
        print("\n🎉 All database connectivity tests passed!")
    else:
        print("\n⚠️ Some database connectivity tests failed. Check the errors above.")
