#!/usr/bin/env python3
"""
Test script to verify User model table name
"""
from app import create_app, db
from app.models import User

def test_user_model():
    """Test the User model table name"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Testing User model...")
        print(f"User model table name: {User.__tablename__}")
        print(f"User model table: {User.__table__}")
        
        # Check if the table exists
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Available tables: {tables}")
        
        if User.__tablename__ in tables:
            print(f"✅ Table '{User.__tablename__}' exists in database")
        else:
            print(f"❌ Table '{User.__tablename__}' NOT found in database")
            
        # Try to query the table
        try:
            user_count = User.query.count()
            print(f"✅ User table query successful. Count: {user_count}")
        except Exception as e:
            print(f"❌ User table query failed: {e}")

if __name__ == "__main__":
    test_user_model()
