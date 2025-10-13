#!/usr/bin/env python3
"""
Check database schema and create missing tables
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
import sqlite3

def check_database_schema():
    app = create_app()
    
    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"📍 Database path: {db_path}")
        
        # Connect directly to SQLite to check tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print(f"📊 Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                print(f"    Columns: {len(columns)}")
                for col in columns:
                    print(f"      {col[1]} ({col[2]})")
                print()
            
            # Create tables if they don't exist
            if not any('user' in table[0] for table in tables):
                print("🔧 Creating user table...")
                db.create_all()
                print("✅ Database tables created")
            else:
                print("✅ User table exists")
                
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    check_database_schema()