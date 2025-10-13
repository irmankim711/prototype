#!/usr/bin/env python3
"""
Add firebase_uid column to user table
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
import sqlite3

def add_firebase_uid_column():
    app = create_app()
    
    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"📍 Database path: {db_path}")
        
        # Connect directly to SQLite to add the column
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if firebase_uid column already exists
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'firebase_uid' in columns:
                print("✅ firebase_uid column already exists")
                return
            
            # Add the firebase_uid column
            cursor.execute("ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(255)")
            
            # Create unique index on firebase_uid
            cursor.execute("CREATE UNIQUE INDEX idx_user_firebase_uid ON user(firebase_uid) WHERE firebase_uid IS NOT NULL")
            
            conn.commit()
            print("✅ Added firebase_uid column to user table")
            
        except sqlite3.Error as e:
            print(f"❌ Error adding firebase_uid column: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    add_firebase_uid_column()