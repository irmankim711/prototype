#!/usr/bin/env python3
"""
Reset database - drop all tables and recreate with current schema
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def reset_database():
    """Drop and recreate all tables"""
    
    print("=" * 50)
    print("RESETTING DATABASE")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.models import User  # Import models to ensure they're registered
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            print("🗑️  Dropping all existing tables...")
            db.drop_all()
            print("✅ All tables dropped!")
            
            print("📋 Creating all tables with current schema...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Check what tables were created
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📋 Tables in database ({len(tables)}):")
            for table in sorted(tables):
                print(f"   - {table}")
                
            # Check user table columns specifically
            if 'user' in tables:
                print(f"\n👤 User table columns:")
                columns = inspector.get_columns('user')
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")
                
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ Database reset completed!")
    return True

if __name__ == "__main__":
    reset_database()
