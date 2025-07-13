#!/usr/bin/env python3
"""
Database connection test script
Run this to diagnose database connection issues
"""

import os
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

def test_database_connection():
    """Test database connection with detailed error reporting"""
    
    # Load environment variables
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables")
        return False
    
    print(f"📋 Database URL: {database_url}")
    
    # Parse the URL to check format
    try:
        parsed = urlparse(database_url)
        print(f"📋 Scheme: {parsed.scheme}")
        print(f"📋 Host: {parsed.hostname}")
        print(f"📋 Port: {parsed.port}")
        print(f"📋 Database: {parsed.path[1:] if parsed.path else 'None'}")
        print(f"📋 Username: {parsed.username}")
        print(f"📋 Password: {'***' if parsed.password else 'None'}")
    except Exception as e:
        print(f"❌ ERROR parsing URL: {e}")
        return False
    
    # Test 1: Raw psycopg2 connection
    print("\n" + "=" * 40)
    print("TEST 1: Raw psycopg2 connection")
    print("=" * 40)
    
    try:
        # Convert URL for psycopg2 if needed
        if database_url.startswith('postgresql+psycopg2://'):
            psycopg2_url = database_url.replace('postgresql+psycopg2://', 'postgresql://')
        else:
            psycopg2_url = database_url
            
        conn = psycopg2.connect(psycopg2_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Raw psycopg2 connection successful!")
        print(f"📋 PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Raw psycopg2 connection failed: {e}")
        print("\n💡 Common solutions:")
        print("   - Check if DATABASE_URL format is correct")
        print("   - Verify username and password")
        print("   - Check if database host is reachable")
        print("   - Ensure psycopg2-binary is installed")
        return False
    
    # Test 2: SQLAlchemy connection
    print("\n" + "=" * 40)
    print("TEST 2: SQLAlchemy connection")
    print("=" * 40)
    
    try:
        # Ensure URL has the right driver
        if database_url.startswith('postgresql://'):
            sqlalchemy_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        else:
            sqlalchemy_url = database_url
            
        engine = create_engine(sqlalchemy_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]
            print(f"✅ SQLAlchemy connection successful!")
            print(f"📋 Connected to database: {db_name}")
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False
    
    # Test 3: Check if tables exist
    print("\n" + "=" * 40)
    print("TEST 3: Check database tables")
    print("=" * 40)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No tables found. You may need to run migrations.")
                print("   Run: flask db upgrade")
    except Exception as e:
        print(f"❌ Failed to check tables: {e}")
    
    print("\n" + "=" * 60)
    print("✅ DATABASE CONNECTION TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_database_connection()
