#!/usr/bin/env python3
"""
Add firebase_uid column directly to the database
"""

import sqlite3
import os

def add_firebase_column():
    # Get database path
    db_path = 'backend/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if firebase_uid column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'firebase_uid' in columns:
            print("✅ firebase_uid column already exists")
            return
        
        # Add the firebase_uid column
        cursor.execute("ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(255)")
        
        # Create unique index on firebase_uid (where not null)
        cursor.execute("CREATE UNIQUE INDEX idx_user_firebase_uid ON user(firebase_uid) WHERE firebase_uid IS NOT NULL")
        
        conn.commit()
        print("✅ Added firebase_uid column to user table")
        
    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_firebase_column()