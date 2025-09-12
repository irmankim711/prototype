#!/usr/bin/env python3
"""
Check database status and tables
"""
import sqlite3
import os

def check_database_status():
    """Check if database exists and has tables"""
    
    print("=== Database Status Check ===")
    
    # Check if database file exists
    db_file = 'app.db'
    if os.path.exists(db_file):
        file_size = os.path.getsize(db_file)
        print(f"✅ Database file exists: {db_file}")
        print(f"   Size: {file_size} bytes")
    else:
        print(f"❌ Database file not found: {db_file}")
        return False
    
    # Check database tables
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Database tables ({len(tables)}):")
        if tables:
            for table in tables:
                table_name = table[0]
                # Get row count for each table
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"   - {table_name}: {count} rows")
                except Exception as e:
                    print(f"   - {table_name}: Error getting count - {e}")
        else:
            print("   No tables found")
        
        # Check database schema
        print(f"\n🔍 Database schema:")
        cursor.execute("PRAGMA table_info(sqlite_master)")
        schema_info = cursor.fetchall()
        print(f"   Schema version: {len(schema_info)} columns")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database_status()
