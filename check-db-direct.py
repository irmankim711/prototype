#!/usr/bin/env python3
"""
Check database directly without SQLAlchemy
"""

import sqlite3
import os

def check_db_direct():
    db_path = 'backend/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check user table specifically
        if any('user' in table[0] for table in tables):
            cursor.execute("PRAGMA table_info(user)")
            columns = cursor.fetchall()
            
            print(f"\n📋 User table columns ({len(columns)}):")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
            
            # Check if there are any users
            cursor.execute("SELECT COUNT(*) FROM user")
            count = cursor.fetchone()[0]
            print(f"\n👥 Users in database: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, email, firebase_uid FROM user LIMIT 5")
                users = cursor.fetchall()
                print("\n📋 Sample users:")
                for user in users:
                    print(f"  - ID: {user[0]}, Email: {user[1]}, Firebase UID: {user[2]}")
        else:
            print("❌ No user table found")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_db_direct()