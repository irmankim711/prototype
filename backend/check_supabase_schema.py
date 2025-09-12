#!/usr/bin/env python3
"""
Check Supabase database schema against model configuration
This will help identify if database tables match the expected models
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

def get_database_connection():
    """Get connection to Supabase database"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return None
            
        print(f"🔗 Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
        
        # Parse connection string
        if database_url.startswith('postgresql://'):
            # Remove postgresql:// prefix
            conn_string = database_url.replace('postgresql://', '')
            
            # Split into parts
            if '@' in conn_string:
                auth_part, host_part = conn_string.split('@', 1)
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                else:
                    username, password = auth_part, ''
                
                if ':' in host_part:
                    host_port, database = host_part.split('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                    else:
                        host, port = host_port, '5432'
                else:
                    host, port, database = host_part, '5432', 'postgres'
            else:
                print("❌ Invalid DATABASE_URL format")
                return None
            
            print(f"📋 Connection details:")
            print(f"   Host: {host}")
            print(f"   Port: {port}")
            print(f"   Database: {database}")
            print(f"   Username: {username}")
            
            # Connect to database
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )
            
            print("✅ Successfully connected to Supabase database!")
            return conn
            
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def check_table_structure(conn):
    """Check what tables exist and their structure"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Found {len(tables)} tables in database:")
        
        for table in tables:
            table_name = table['table_name']
            print(f"\n🔍 Table: {table_name}")
            
            # Get table columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            print(f"   Columns ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"     - {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        cursor.close()
        return tables
        
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return []

def check_expected_tables():
    """Check if expected tables exist based on models"""
    expected_tables = [
        'users',           # User model
        'user_tokens',     # UserToken model  
        'user_sessions',   # UserSession model
        'programs',        # Program model
        'participants',    # Participant model
        'attendance_records', # AttendanceRecord model
        'form_integrations',  # FormIntegration model
        'form_responses',     # FormResponse model
        'reports',         # Report model
        'report_templates' # ReportTemplate model
    ]
    
    print(f"\n🎯 Expected tables based on models:")
    for table in expected_tables:
        print(f"   - {table}")
    
    return expected_tables

def check_table_mismatches(existing_tables, expected_tables):
    """Check for mismatches between existing and expected tables"""
    existing_set = {table['table_name'] for table in existing_tables}
    expected_set = set(expected_tables)
    
    missing_tables = expected_set - existing_set
    extra_tables = existing_set - expected_set
    
    print(f"\n🔍 Table Analysis:")
    
    if missing_tables:
        print(f"❌ Missing tables ({len(missing_tables)}):")
        for table in sorted(missing_tables):
            print(f"   - {table}")
    else:
        print("✅ All expected tables exist!")
    
    if extra_tables:
        print(f"⚠️  Extra tables ({len(extra_tables)}):")
        for table in sorted(extra_tables):
            print(f"   - {table}")
    
    return missing_tables, extra_tables

def check_user_table_structure(conn):
    """Specifically check the users table structure"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        users_table_exists = cursor.fetchone()['exists']
        
        if not users_table_exists:
            print("\n❌ Users table does not exist!")
            return False
        
        print("\n👥 Users table structure:")
        
        # Get users table columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # Check for critical columns
        critical_columns = ['id', 'email', 'username', 'password_hash']
        existing_columns = {col['column_name'] for col in columns}
        missing_critical = [col for col in critical_columns if col not in existing_columns]
        
        if missing_critical:
            print(f"\n❌ Missing critical columns: {missing_critical}")
            return False
        else:
            print(f"\n✅ All critical columns exist!")
            return True
            
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error checking users table: {e}")
        return False

def main():
    """Main function to check database schema"""
    print("=" * 60)
    print("🔍 SUPABASE DATABASE SCHEMA CHECK")
    print("=" * 60)
    
    # Connect to database
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        # Check table structure
        existing_tables = check_table_structure(conn)
        
        # Check expected tables
        expected_tables = check_expected_tables()
        
        # Check for mismatches
        missing_tables, extra_tables = check_table_mismatches(existing_tables, expected_tables)
        
        # Specifically check users table
        users_table_ok = check_user_table_structure(conn)
        
        # Summary
        print(f"\n" + "=" * 60)
        print("📊 SCHEMA ANALYSIS SUMMARY")
        print("=" * 60)
        
        if missing_tables:
            print(f"❌ CRITICAL: {len(missing_tables)} expected tables are missing")
            print("   This could cause sign-in and other functionality issues!")
            print("\n💡 Solution: Run database migrations or initialize database")
        else:
            print("✅ All expected tables exist")
        
        if not users_table_ok:
            print("❌ CRITICAL: Users table structure is incomplete")
            print("   This will definitely cause sign-in issues!")
        else:
            print("✅ Users table structure is correct")
        
        if extra_tables:
            print(f"⚠️  Note: {len(extra_tables)} extra tables found (usually not a problem)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if missing_tables:
            print("   1. Run: python init_db.py")
            print("   2. Run: python -m flask db upgrade")
            print("   3. Check if migrations are up to date")
        
        if not users_table_ok:
            print("   1. Drop and recreate users table")
            print("   2. Ensure User model is properly imported")
            print("   3. Run database initialization")
        
    finally:
        conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main()
