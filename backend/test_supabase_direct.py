#!/usr/bin/env python3
"""
Direct Supabase connection test
"""

import os
import psycopg2
from urllib.parse import urlparse

def test_supabase_connection():
    """Test direct connection to Supabase"""
    
    database_url = "postgresql://postgres.kprvqvugkggcpqwsisnz:0BQRPIQzMcqQAM43@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
    
    print("🔍 Testing Supabase connection...")
    print(f"📍 URL: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
    
    try:
        # Parse URL
        url_parts = urlparse(database_url)
        
        print(f"   Host: {url_parts.hostname}")
        print(f"   Port: {url_parts.port}")  
        print(f"   Database: {url_parts.path[1:]}")
        print(f"   User: {url_parts.username}")
        
        # Test connection
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection successful!")
        print(f"   Database version: {version[0][:50]}...")
        
        # Check if report_templates table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'report_templates';
        """)
        
        table_exists = cursor.fetchone()
        if table_exists:
            print(f"✅ report_templates table exists")
            
            # Count existing templates
            cursor.execute("SELECT COUNT(*) FROM report_templates;")
            count = cursor.fetchone()[0]
            print(f"   Current templates in database: {count}")
            
        else:
            print(f"❌ report_templates table does not exist")
            
            # List all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            print(f"   Available tables ({len(tables)}):")
            for table in tables[:10]:  # Show first 10
                print(f"     - {table[0]}")
            if len(tables) > 10:
                print(f"     ... and {len(tables) - 10} more")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {str(e)}")
        if "Wrong password" in str(e):
            print("   💡 Password may have been changed. Check Supabase dashboard for current credentials.")
        elif "timeout" in str(e).lower():
            print("   💡 Connection timeout. Check network connectivity.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == '__main__':
    test_supabase_connection()