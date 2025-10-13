#!/usr/bin/env python3
"""
Database Schema Checker
Checks the current database schema and compares it with model definitions
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database_schema():
    """Check the current database schema"""
    try:
        import psycopg2
        
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return False
            
        print(f"🔗 Connecting to database: {database_url.split('@')[1] if '@' in database_url else database_url}")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("\n📋 Checking database schema...")
        
        # Check if users table exists
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"\n📊 Tables in database ({len(tables)}):")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check users table schema
        if ('users',) in tables:
            print("\n👥 Users table schema:")
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            
            for col in columns:
                col_name, data_type, nullable, default, max_length = col
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                length_str = f"({max_length})" if max_length else ""
                print(f"   - {col_name}: {data_type}{length_str} {nullable_str}{default_str}")
        else:
            print("\n❌ Users table does not exist!")
        
        # Check for any constraints
        cur.execute("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'users';
        """)
        constraints = cur.fetchall()
        
        if constraints:
            print("\n🔒 Users table constraints:")
            for constraint in constraints:
                print(f"   - {constraint[0]}: {constraint[1]}")
        
        cur.close()
        conn.close()
        
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_model_definitions():
    """Check the model definitions"""
    print("\n🔍 Checking model definitions...")
    
    try:
        # Add backend directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app.models import User
        
        print("✅ User model imported successfully")
        
        # Check User model attributes
        print(f"📝 User model table name: {User.__tablename__}")
        print(f"📝 User model columns:")
        
        for column in User.__table__.columns:
            print(f"   - {column.name}: {column.type} (nullable: {column.nullable})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_schema_and_models():
    """Compare database schema with model definitions"""
    print("\n🔍 Comparing database schema with model definitions...")
    
    try:
        import psycopg2
        
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Get database columns
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        db_columns = {row[0] for row in cur.fetchall()}
        
        # Get model columns
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.models import User
        model_columns = {column.name for column in User.__table__.columns}
        
        print(f"\n📊 Database columns ({len(db_columns)}): {sorted(db_columns)}")
        print(f"📊 Model columns ({len(model_columns)}): {sorted(model_columns)}")
        
        # Find differences
        missing_in_db = model_columns - db_columns
        extra_in_db = db_columns - model_columns
        
        if missing_in_db:
            print(f"\n❌ Columns missing in database: {sorted(missing_in_db)}")
        
        if extra_in_db:
            print(f"\n⚠️  Extra columns in database: {sorted(extra_in_db)}")
            
        if not missing_in_db and not extra_in_db:
            print("\n✅ Database schema matches model definition!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error comparing schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE SCHEMA CHECKER")
    print("=" * 60)
    
    # Check database schema
    if check_database_schema():
        # Check model definitions
        if check_model_definitions():
            # Compare both
            compare_schema_and_models()
    
    print("\n" + "=" * 60)
