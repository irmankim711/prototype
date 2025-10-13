#!/usr/bin/env python3
"""
Fix database schema by adding firebase_uid column
"""

import sqlite3
import os

def fix_database_schema():
    # Database path
    db_path = 'backend/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current table schema
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        print("📊 Current user table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Check if firebase_uid exists
        column_names = [col[1] for col in columns]
        
        if 'firebase_uid' not in column_names:
            print("\n🔧 Adding firebase_uid column...")
            cursor.execute("ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(255)")
            
            # Create unique index
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_firebase_uid ON user(firebase_uid) WHERE firebase_uid IS NOT NULL")
            
            conn.commit()
            print("✅ Added firebase_uid column successfully")
        else:
            print("✅ firebase_uid column already exists")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(user)")
        new_columns = cursor.fetchall()
        
        print("\n📊 Updated user table schema:")
        for col in new_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print("\n✅ Database schema fixed successfully!")
    else:
        print("\n❌ Failed to fix database schema")