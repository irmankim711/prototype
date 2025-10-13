#!/usr/bin/env python3
"""
Fix the reports table schema mismatch between backend models and Supabase
"""

import os
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres.kprvqvugkggcpqwsisnz:0BQRPIQzMcqQAM43@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def get_current_schema():
    """Get current reports table schema"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'reports'
            ORDER BY ordinal_position;
        """)
        
        current_columns = {}
        for row in cursor.fetchall():
            current_columns[row[0]] = {
                'type': row[1],
                'nullable': row[2],
                'default': row[3]
            }
        
        cursor.close()
        conn.close()
        return current_columns
        
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return {}

def fix_reports_schema():
    """Fix the reports table schema to match backend expectations"""
    
    logger.info("🔧 Fixing reports table schema...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get current schema
        current_schema = get_current_schema()
        logger.info(f"📋 Current schema has {len(current_schema)} columns")
        
        # Required columns that are missing
        required_columns = [
            {
                'name': 'program_id',
                'type': 'INTEGER',
                'nullable': True,
                'default': None
            },
            {
                'name': 'generation_status',
                'type': 'VARCHAR(20)',
                'nullable': True,
                'default': "'pending'"
            },
            {
                'name': 'generated_at',
                'type': 'TIMESTAMP WITH TIME ZONE',
                'nullable': True,
                'default': None
            },
            {
                'name': 'generation_time_seconds',
                'type': 'INTEGER',
                'nullable': True,
                'default': None
            },
            {
                'name': 'file_size',
                'type': 'INTEGER',
                'nullable': True,
                'default': None
            },
            {
                'name': 'file_format',
                'type': 'VARCHAR(10)',
                'nullable': True,
                'default': None
            },
            {
                'name': 'download_url',
                'type': 'VARCHAR(500)',
                'nullable': True,
                'default': None
            },
            {
                'name': 'last_downloaded',
                'type': 'TIMESTAMP WITH TIME ZONE',
                'nullable': True,
                'default': None
            },
            {
                'name': 'data_source',
                'type': 'JSONB',
                'nullable': True,
                'default': None
            },
            {
                'name': 'generation_config',
                'type': 'JSONB',
                'nullable': True,
                'default': None
            },
            {
                'name': 'completeness_score',
                'type': 'INTEGER',
                'nullable': True,
                'default': None
            },
            {
                'name': 'processing_notes',
                'type': 'TEXT',
                'nullable': True,
                'default': None
            },
            {
                'name': 'created_by',
                'type': 'VARCHAR(255)',
                'nullable': True,
                'default': None
            }
        ]
        
        # Add missing columns
        added_columns = []
        for column in required_columns:
            if column['name'] not in current_schema:
                sql = f"""
                ALTER TABLE reports 
                ADD COLUMN {column['name']} {column['type']}
                """
                
                if column['default']:
                    sql += f" DEFAULT {column['default']}"
                
                if not column['nullable']:
                    sql += " NOT NULL"
                
                sql += ";"
                
                logger.info(f"Adding column: {column['name']}")
                cursor.execute(sql)
                added_columns.append(column['name'])
        
        # Rename template_id to match UUID format if needed
        if 'template_id' not in current_schema and 'template_id' in current_schema:
            logger.info("Renaming template_id column...")
            cursor.execute("ALTER TABLE reports RENAME COLUMN template_id TO template_id;")
        
        # Create an alias for generation_status if we have status
        if 'status' in current_schema and 'generation_status' not in current_schema:
            logger.info("Creating generation_status as alias for status...")
            cursor.execute("ALTER TABLE reports ADD COLUMN generation_status VARCHAR(20);")
            cursor.execute("UPDATE reports SET generation_status = status WHERE status IS NOT NULL;")
            added_columns.append('generation_status')
        
        # Commit changes
        conn.commit()
        
        logger.info(f"✅ Added {len(added_columns)} columns to reports table:")
        for col in added_columns:
            logger.info(f"   • {col}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing schema: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False

def create_minimal_report_model():
    """Create a minimal report model that matches the current Supabase schema"""
    
    minimal_model = '''
# backend/app/models/minimal_report.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MinimalReport(Base):
    """Minimal report model that matches current Supabase schema"""
    __tablename__ = 'reports'
    
    # Core fields that exist in Supabase
    id = Column(String, primary_key=True)  # UUID in Supabase
    title = Column(String, nullable=False)
    description = Column(Text)
    report_type = Column(String, nullable=False)
    status = Column(String, default='pending')
    
    # File info
    file_url = Column(Text)
    file_size = Column(Integer)
    file_format = Column(String)
    
    # Metadata
    parameters = Column(JSON)
    data_snapshot = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Tracking
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'status': self.status,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'view_count': self.view_count,
            'download_count': self.download_count
        }
'''
    
    logger.info("💡 ALTERNATIVE SOLUTION:")
    logger.info("You can create a minimal report model that matches the current schema:")
    print(minimal_model)
    return minimal_model

def main():
    """Main execution function"""
    print("🔧 REPORTS SCHEMA MISMATCH FIX")
    print("=" * 50)
    print("This script will add missing columns to match the backend model expectations.")
    print()
    
    # Show current schema
    current = get_current_schema()
    print(f"📋 Current Supabase schema has {len(current)} columns:")
    for col_name in sorted(current.keys()):
        print(f"   • {col_name}")
    
    print(f"\n🔧 Backend model expects additional columns like:")
    print(f"   • program_id, generation_status, generated_at, etc.")
    
    # Option 1: Fix the schema
    print(f"\n🎯 OPTION 1: Add missing columns to Supabase")
    fix_success = fix_reports_schema()
    
    if fix_success:
        print("✅ Schema fix completed!")
        print("💡 The backend should now work with the reports table.")
    else:
        print("❌ Schema fix failed!")
        
        # Option 2: Alternative minimal model
        print(f"\n🎯 OPTION 2: Use a minimal report model")
        create_minimal_report_model()
        
        print(f"\n💡 To use the minimal model:")
        print(f"   1. Save the code above as backend/app/models/minimal_report.py")
        print(f"   2. Import MinimalReport instead of Report in your routes")
        print(f"   3. This avoids schema mismatches")

if __name__ == '__main__':
    main()
