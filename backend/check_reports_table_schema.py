#!/usr/bin/env python3
"""
Check the actual reports table schema in Supabase
to understand the column mismatch
"""

import os
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres.kprvqvugkggcpqwsisnz:0BQRPIQzMcqQAM43@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def check_reports_table_schema():
    """Check the actual reports table schema"""
    
    logger.info("🔍 Checking reports table schema in Supabase...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        logger.info("✅ Connected to Supabase database")
        
        # Check if reports table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'reports'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            logger.info("✅ Reports table exists")
            
            # Get table schema
            cursor.execute("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'reports'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            logger.info(f"📋 Reports table schema ({len(columns)} columns):")
            logger.info("Column                    Type                 Nullable   Default")
            logger.info("-" * 70)
            
            status_column_exists = False
            generation_status_exists = False
            
            for column in columns:
                column_name, data_type, is_nullable, column_default = column
                nullable = "YES" if is_nullable == "YES" else "NO"
                default = column_default if column_default else "None"
                logger.info(f"{column_name:25} {data_type:20} {nullable:10} {default}")
                
                if column_name == "status":
                    status_column_exists = True
                elif column_name == "generation_status":
                    generation_status_exists = True
            
            logger.info("\n🔍 Status column analysis:")
            logger.info(f"   'status' column exists: {status_column_exists}")
            logger.info(f"   'generation_status' column exists: {generation_status_exists}")
            
            # Count existing reports
            cursor.execute("SELECT COUNT(*) FROM reports;")
            report_count = cursor.fetchone()[0]
            logger.info(f"\n📊 Current reports in table: {report_count}")
            
            return {
                "exists": True,
                "columns": columns,
                "has_status": status_column_exists,
                "has_generation_status": generation_status_exists,
                "report_count": report_count
            }
            
        else:
            logger.warning("❌ Reports table does not exist!")
            return {"exists": False}
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error checking reports table: {e}")
        return {"exists": False, "error": str(e)}

def main():
    """Main execution function"""
    print("🔍 REPORTS TABLE SCHEMA CHECK")
    print("=" * 50)
    
    result = check_reports_table_schema()
    
    if result.get("exists"):
        print("\n💡 RECOMMENDATIONS:")
        
        if not result.get("has_status") and not result.get("has_generation_status"):
            print("❌ Neither 'status' nor 'generation_status' columns exist")
            print("🔧 SOLUTION: Add the status column to Supabase:")
            print("   ALTER TABLE reports ADD COLUMN status TEXT DEFAULT 'generated';")
            
        elif result.get("has_generation_status") and not result.get("has_status"):
            print("⚠️ Table has 'generation_status' but code expects 'status'")
            print("🔧 SOLUTION OPTIONS:")
            print("   A) Add 'status' column: ALTER TABLE reports ADD COLUMN status TEXT DEFAULT 'generated';")
            print("   B) Update backend code to use 'generation_status' instead of 'status'")
            
        elif result.get("has_status"):
            print("✅ 'status' column exists - check backend code for typos")
            
    else:
        print("❌ Reports table doesn't exist - need to create it first!")

if __name__ == '__main__':
    main()
