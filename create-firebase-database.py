#!/usr/bin/env python3
"""
Create Firebase-compatible database with correct schema
"""

import os
import sys
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
backend_path = Path(__file__).parent / 'backend'
env_path = backend_path / '.env'
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(backend_path))

def create_database_with_schema():
    """Create database with proper schema including firebase_uid"""
    print("🔧 Creating Firebase-compatible database...")
    
    # Create database in the correct location
    db_path = backend_path / 'app.db'
    
    print(f"📁 Database path: {db_path}")
    
    # Remove existing database if it exists
    if db_path.exists():
        print("🗑️  Removing existing database...")
        db_path.unlink()
    
    # Create new database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Create user table with firebase_uid column
        print("📊 Creating user table with Firebase support...")
        cursor.execute('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                firebase_uid VARCHAR(255) UNIQUE,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                username VARCHAR(50) UNIQUE,
                phone VARCHAR(20),
                company VARCHAR(100),
                job_title VARCHAR(100),
                bio TEXT,
                avatar_url VARCHAR(255),
                is_active BOOLEAN DEFAULT 1,
                role TEXT DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Create unique index for firebase_uid
        cursor.execute('''
            CREATE UNIQUE INDEX idx_user_firebase_uid 
            ON user(firebase_uid) 
            WHERE firebase_uid IS NOT NULL
        ''')
        
        # Create a test user for verification
        print("👤 Creating test user...")
        cursor.execute('''
            INSERT INTO user (
                email, first_name, last_name, username, is_active, role
            ) VALUES (
                'test@example.com', 'Test', 'User', 'testuser', 1, 'user'
            )
        ''')
        
        conn.commit()
        
        # Verify the schema
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        print("\n📊 Created user table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verify firebase_uid column exists
        column_names = [col[1] for col in columns]
        if 'firebase_uid' in column_names:
            print("✅ firebase_uid column created successfully")
        else:
            print("❌ firebase_uid column missing")
            return False
        
        # Test user count
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"✅ Database created with {user_count} test user(s)")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database creation failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def test_flask_database_connection():
    """Test if Flask can connect to the database"""
    print("\n🧪 Testing Flask database connection...")
    
    try:
        from app import create_app, db
        from app.models.production.user_models import User
        
        app = create_app()
        with app.app_context():
            # Test database query
            user_count = User.query.count()
            print(f"✅ Flask can connect to database. User count: {user_count}")
            
            # Test creating a Firebase user
            test_user = User(
                email="firebase-test@example.com",
                firebase_uid="test-firebase-uid-12345",
                first_name="Firebase",
                last_name="Test",
                username="firebasetest",
                is_active=True
            )
            
            # Test to_dict method
            user_dict = test_user.to_dict()
            print(f"✅ User to_dict() method works: {user_dict['email']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Flask database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Create Firebase-compatible database"""
    print("🔥 Firebase Database Setup")
    print("=" * 50)
    
    # Step 1: Create database with schema
    db_created = create_database_with_schema()
    
    if not db_created:
        print("❌ Failed to create database")
        return False
    
    # Step 2: Test Flask connection
    flask_ok = test_flask_database_connection()
    
    if not flask_ok:
        print("❌ Flask database connection failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Firebase database setup completed successfully!")
    print("\n💡 Next steps:")
    print("1. Restart the backend server")
    print("2. Test Firebase authentication")
    print("3. Try logging in from the frontend")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)