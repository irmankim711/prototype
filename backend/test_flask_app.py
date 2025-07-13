#!/usr/bin/env python3
"""
Simple test to verify Flask app and database connectivity
"""

from app import create_app
import requests
import time
import threading

def test_app():
    """Test the Flask app"""
    app = create_app()
    
    print("=" * 50)
    print("FLASK APP TEST")
    print("=" * 50)
    
    # Test app creation
    print("✅ Flask app created successfully!")
    
    # Test with app context
    with app.app_context():
        from app import db
        try:
            # Simple database query
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1")).fetchone()
            print("✅ Database query successful!")
            print(f"   Result: {result[0]}")
            
            # Count tables
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchone()
            print(f"✅ Found {result[0]} tables in database")
            
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("Your database connection is working perfectly! 🎉")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_app()
