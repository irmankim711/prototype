#!/usr/bin/env python3
"""
Check the actual schema of report_templates table in Supabase
"""

import psycopg2

DATABASE_URL = "postgresql://postgres.kprvqvugkggcpqwsisnz:0BQRPIQzMcqQAM43@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def check_table_schema():
    """Check the actual table schema"""
    
    print("🔍 Checking report_templates table schema in Supabase...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get column information
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'report_templates' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print(f"✅ Found report_templates table with {len(columns)} columns:")
            print(f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default'}")
            print("-" * 70)
            
            for col in columns:
                column_name, data_type, is_nullable, default = col
                nullable = "YES" if is_nullable == 'YES' else "NO"
                default_str = str(default)[:20] if default else "None"
                print(f"{column_name:<25} {data_type:<20} {nullable:<10} {default_str}")
        
        else:
            print("❌ report_templates table not found")
            
        # Also check all tables to see what's available
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Available tables in database ({len(tables)}):")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")

if __name__ == '__main__':
    check_table_schema()