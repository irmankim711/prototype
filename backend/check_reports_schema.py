#!/usr/bin/env python3
"""
Check actual reports table schema vs code expectations
"""

import sys
sys.path.append('.')

from app import create_app, db
from sqlalchemy import text

def check_reports_schema():
    """Check the actual reports table schema"""
    print("🔍 Checking Reports Table Schema...")
    
    app = create_app()
    with app.app_context():
        try:
            # Reset any failed transaction first
            db.session.rollback()
            
            # Get actual table schema
            schema_query = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'reports'
                ORDER BY ordinal_position
            """)
            
            result = db.session.execute(schema_query)
            columns = result.fetchall()
            
            print(f"✅ Found {len(columns)} columns in reports table:")
            print("\n📋 ACTUAL DATABASE SCHEMA:")
            print("-" * 60)
            
            actual_columns = []
            for col in columns:
                print(f"   {col.column_name:<25} | {col.data_type:<15} | {'NULL' if col.is_nullable == 'YES' else 'NOT NULL'}")
                actual_columns.append(col.column_name)
            
            print("\n🔧 COLUMNS EXPECTED BY CODE:")
            print("-" * 60)
            expected_columns = [
                'id', 'program_id', 'template_id', 'title', 'description', 
                'report_type', 'generation_status', 'generated_at', 
                'generation_time_seconds', 'file_path', 'file_size', 
                'file_format', 'download_url', 'download_count', 
                'last_downloaded', 'data_source', 'generation_config', 
                'error_message', 'completeness_score', 'processing_notes', 
                'created_by', 'created_at', 'user_id'
            ]
            
            missing_columns = []
            for col in expected_columns:
                if col in actual_columns:
                    print(f"   ✅ {col}")
                else:
                    print(f"   ❌ {col} - MISSING")
                    missing_columns.append(col)
            
            print("\n📊 SCHEMA ANALYSIS:")
            print(f"   Columns in database: {len(actual_columns)}")
            print(f"   Columns expected: {len(expected_columns)}")
            print(f"   Missing columns: {len(missing_columns)}")
            
            if missing_columns:
                print(f"\n🔧 MISSING COLUMNS TO ADD:")
                for col in missing_columns:
                    print(f"   - {col}")
                
                print(f"\n💡 QUICK SQL FIX:")
                print("-- Add missing columns to reports table")
                sql_fixes = {
                    'data_source': 'ALTER TABLE reports ADD COLUMN data_source JSONB;',
                    'generation_config': 'ALTER TABLE reports ADD COLUMN generation_config JSONB;', 
                    'completeness_score': 'ALTER TABLE reports ADD COLUMN completeness_score NUMERIC;',
                    'processing_notes': 'ALTER TABLE reports ADD COLUMN processing_notes TEXT;',
                    'error_message': 'ALTER TABLE reports ADD COLUMN error_message TEXT;',
                    'generation_time_seconds': 'ALTER TABLE reports ADD COLUMN generation_time_seconds INTEGER;',
                    'file_size': 'ALTER TABLE reports ADD COLUMN file_size BIGINT;',
                    'download_count': 'ALTER TABLE reports ADD COLUMN download_count INTEGER DEFAULT 0;',
                    'last_downloaded': 'ALTER TABLE reports ADD COLUMN last_downloaded TIMESTAMP;',
                }
                
                for col in missing_columns:
                    if col in sql_fixes:
                        print(sql_fixes[col])
                    else:
                        print(f"-- TODO: Define proper type for {col}")
            else:
                print("✅ All expected columns are present!")
            
            return actual_columns, missing_columns
            
        except Exception as e:
            print(f"❌ Schema check failed: {e}")
            return [], []

def create_minimal_insert_query(actual_columns):
    """Create a safe INSERT query with only existing columns"""
    print("\n🛠️  CREATING SAFE INSERT QUERY...")
    
    # Core columns that should exist
    core_columns = ['id', 'title', 'description', 'report_type', 'generation_status', 'created_at']
    
    # Optional columns to include if they exist
    optional_columns = ['template_id', 'user_id', 'program_id']
    
    safe_columns = []
    for col in core_columns + optional_columns:
        if col in actual_columns:
            safe_columns.append(col)
    
    print(f"✅ Safe columns to use: {safe_columns}")
    
    # Generate safe INSERT query
    placeholders = ', '.join([f':{col}' for col in safe_columns])
    insert_query = f"""
        INSERT INTO reports ({', '.join(safe_columns)})
        VALUES ({placeholders})
        RETURNING id
    """
    
    print(f"\n📝 SAFE INSERT QUERY:")
    print(insert_query)
    
    return safe_columns, insert_query

def main():
    """Check schema and provide fixes"""
    print("🎯 Reports Table Schema Analysis")
    print("=" * 60)
    
    actual_columns, missing_columns = check_reports_schema()
    
    if actual_columns:
        safe_columns, safe_query = create_minimal_insert_query(actual_columns)
        
        print(f"\n🚀 IMMEDIATE SOLUTION:")
        print(f"   Use only the {len(safe_columns)} safe columns for testing")
        print(f"   Add missing columns later for full functionality")
        
        return True
    else:
        print("💥 Cannot analyze schema")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)