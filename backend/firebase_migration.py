#!/usr/bin/env python3
"""
Firebase Migration Script
Adds firebase_uid column to user table for Firebase OAuth integration
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.env_loader import load_environment

def run_migration():
    """Run the Firebase migration"""
    print("🚀 Starting Firebase OAuth Migration...")
    
    # Load environment variables
    try:
        load_environment()
        print("✅ Environment variables loaded")
    except Exception as e:
        print(f"⚠️ Environment loading issue: {e}")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    print(f"📊 Database URL: {database_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check if firebase_uid column already exists
        inspector = inspect(engine)
        columns = inspector.get_columns('user')
        column_names = [col['name'] for col in columns]
        
        if 'firebase_uid' in column_names:
            print("✅ firebase_uid column already exists - no migration needed")
            return True
        
        print("📝 Adding firebase_uid column to user table...")
        
        # Add firebase_uid column
        with engine.connect() as conn:
            if 'sqlite' in database_url:
                # SQLite syntax
                conn.execute(text("ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(255)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_firebase_uid ON user(firebase_uid)"))
            else:
                # PostgreSQL syntax
                conn.execute(text("ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(255) UNIQUE"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_firebase_uid ON user(firebase_uid)"))
            
            conn.commit()
            print("✅ firebase_uid column added successfully")
        
        # Make password_hash nullable for Firebase users
        print("📝 Making password_hash column nullable...")
        
        with engine.connect() as conn:
            if 'sqlite' in database_url:
                # SQLite doesn't support ALTER COLUMN, so we'll skip this for SQLite
                # The model change will handle nullable passwords
                print("ℹ️ SQLite detected - password_hash nullability handled by model")
            else:
                # PostgreSQL syntax
                conn.execute(text("ALTER TABLE user ALTER COLUMN password_hash DROP NOT NULL"))
                conn.commit()
            
            print("✅ password_hash column updated for Firebase compatibility")
        
        print("🎉 Firebase migration completed successfully!")
        print("")
        print("Next steps:")
        print("1. Restart your backend server")
        print("2. Test Firebase authentication endpoints")
        print("3. Update frontend to use Firebase auth context")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def rollback_migration():
    """Rollback the Firebase migration"""
    print("🔄 Rolling back Firebase OAuth Migration...")
    
    # Load environment variables
    try:
        load_environment()
        print("✅ Environment variables loaded")
    except Exception as e:
        print(f"⚠️ Environment loading issue: {e}")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    print(f"📊 Database URL: {database_url}")
    
    try:
        engine = create_engine(database_url)
        
        print("📝 Removing firebase_uid column from user table...")
        
        with engine.connect() as conn:
            if 'sqlite' in database_url:
                # SQLite doesn't support DROP COLUMN, so we'll leave the column
                print("ℹ️ SQLite detected - firebase_uid column will remain (safe to ignore)")
            else:
                # PostgreSQL syntax
                conn.execute(text("DROP INDEX IF EXISTS idx_user_firebase_uid"))
                conn.execute(text("ALTER TABLE user DROP COLUMN IF EXISTS firebase_uid"))
                conn.commit()
                print("✅ firebase_uid column removed successfully")
        
        print("🎉 Firebase migration rollback completed!")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Firebase OAuth Migration Script")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)