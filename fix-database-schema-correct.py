#!/usr/bin/env python3
"""
Fix database schema by adding firebase_uid column to the correct database
"""

import sqlite3
import os
from pathlib import Path

def fix_database_schema():
    # The Flask app uses DATABASE_URL=sqlite:///app.db
    # This creates app.db in the backend directory when running from backend/
    # But when running from root, it creates app.db in the root directory
    
    possible_db_paths = [
        'app.db',  # Root directory (when running from root)
        'backend/app.db',  # Backend directory
        Path(__file__).parent / 'backend' / 'app.db'  # Absolute path to backend
    ]
    
    print("🔍 Looking for database files...")
    
    for db_path in possible_db_paths:
        if os.path.exists(db_path):
            print(f"📁 Found database: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Check current table schema
                cursor.execute("PRAGMA table_info(user)")
                columns = cursor.fetchall()
                
                if not columns:
                    print(f"⚠️  No 'user' table found in {db_path}")
                    conn.close()
                    continue
                
                print(f"\n📊 Current user table schema in {db_path}:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # Check if firebase_uid exists
                column_names = [col[1] for col in columns]
                
                if 'firebase_uid' not in column_names:
                    print(f"\n🔧 Adding firebase_uid column to {db_path}...")
                    cursor.execute("ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(255)")
                    
                    # Create unique index
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_firebase_uid ON user(firebase_uid) WHERE firebase_uid IS NOT NULL")
                    
                    conn.commit()
                    print(f"✅ Added firebase_uid column to {db_path}")
                else:
                    print(f"✅ firebase_uid column already exists in {db_path}")
                
                # Verify the change
                cursor.execute("PRAGMA table_info(user)")
                new_columns = cursor.fetchall()
                
                print(f"\n📊 Updated user table schema in {db_path}:")
                for col in new_columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                conn.close()
                print(f"✅ Successfully processed {db_path}")
                
            except sqlite3.Error as e:
                print(f"❌ Database error in {db_path}: {e}")
                conn.rollback()
                conn.close()
        else:
            print(f"❌ Database not found: {db_path}")
    
    return True

if __name__ == "__main__":
    print("🔧 Database Schema Fix - Finding and Updating All Databases")
    print("=" * 60)
    
    success = fix_database_schema()
    
    if success:
        print("\n✅ Database schema fix completed!")
        print("\n💡 Next steps:")
        print("1. Restart the backend server")
        print("2. Test the Firebase sync endpoint")
    else:
        print("\n❌ Failed to fix database schema")