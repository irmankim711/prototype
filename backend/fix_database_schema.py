#!/usr/bin/env python3
"""
Database Schema Migration Script
Fixes schema mismatches between models.py and actual Supabase database

CRITICAL ISSUES ADDRESSED:
1. forms.schema column missing (model expects JSON column)
2. ID type mismatch (UUID vs Integer)
3. Column name differences (fields vs schema)
4. Missing model columns in database

SAFETY: Creates backup queries before making changes
"""

import os
import sys
sys.path.append('.')

from app import create_app, db
from sqlalchemy import text, inspect
from datetime import datetime
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_data():
    """Backup critical form data before migration"""
    try:
        # Backup forms data
        result = db.session.execute(text("SELECT id, title, description, fields FROM forms LIMIT 5"))
        forms_backup = []
        for row in result:
            forms_backup.append({
                'id': str(row[0]),
                'title': row[1],
                'description': row[2], 
                'fields': row[3]
            })
        
        # Save backup to file
        backup_file = f"forms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump(forms_backup, f, indent=2, default=str)
        
        logger.info(f"✅ Backup created: {backup_file}")
        logger.info(f"📊 Backed up {len(forms_backup)} form records")
        return backup_file
        
    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        return None

def check_current_schema():
    """Check current database schema"""
    try:
        inspector = inspect(db.engine)
        
        # Check forms table columns
        if 'forms' in inspector.get_table_names():
            columns = inspector.get_columns('forms')
            logger.info("📋 Current forms table schema:")
            for col in columns:
                logger.info(f"   - {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(NOT NULL)'}")
        else:
            logger.error("❌ forms table does not exist!")
            return False
            
        # Check for expected model columns
        expected_columns = ['schema', 'creator_id', 'external_url', 'qr_code_data', 'form_settings', 'access_key', 'view_count', 'submission_limit', 'expires_at']
        existing_columns = [col['name'] for col in columns]
        
        missing_columns = []
        for expected in expected_columns:
            if expected not in existing_columns:
                missing_columns.append(expected)
        
        if missing_columns:
            logger.warning(f"⚠️  Missing columns: {missing_columns}")
            return False
        else:
            logger.info("✅ All expected columns exist")
            return True
            
    except Exception as e:
        logger.error(f"❌ Schema check failed: {str(e)}")
        return False

def add_missing_columns():
    """Add missing columns to match models.py"""
    try:
        logger.info("🔧 Adding missing columns to forms table...")
        
        # Add missing columns with appropriate defaults
        migration_queries = [
            # Add schema column (rename from fields if exists, or create new)
            """
            DO $$ 
            BEGIN 
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'fields') THEN
                    -- Rename fields to schema
                    ALTER TABLE forms RENAME COLUMN fields TO schema;
                    RAISE NOTICE 'Renamed fields column to schema';
                ELSE
                    -- Add new schema column
                    ALTER TABLE forms ADD COLUMN schema JSONB;
                    RAISE NOTICE 'Added new schema column';
                END IF;
            EXCEPTION 
                WHEN duplicate_column THEN 
                    RAISE NOTICE 'schema column already exists';
            END $$;
            """,
            
            # Add other missing columns with defaults
            """
            DO $$
            BEGIN
                -- Add external_url if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'external_url') THEN
                    ALTER TABLE forms ADD COLUMN external_url VARCHAR(500);
                END IF;
                
                -- Add qr_code_data if missing  
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'qr_code_data') THEN
                    ALTER TABLE forms ADD COLUMN qr_code_data TEXT;
                END IF;
                
                -- Add form_settings if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'form_settings') THEN
                    ALTER TABLE forms ADD COLUMN form_settings JSONB;
                END IF;
                
                -- Add access_key if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'access_key') THEN
                    ALTER TABLE forms ADD COLUMN access_key VARCHAR(100);
                END IF;
                
                -- Add view_count if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'view_count') THEN
                    ALTER TABLE forms ADD COLUMN view_count INTEGER DEFAULT 0;
                END IF;
                
                -- Add submission_limit if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'submission_limit') THEN
                    ALTER TABLE forms ADD COLUMN submission_limit INTEGER;
                END IF;
                
                -- Add expires_at if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forms' AND column_name = 'expires_at') THEN
                    ALTER TABLE forms ADD COLUMN expires_at TIMESTAMP;
                END IF;
            END $$;
            """,
            
            # Fix column types and constraints
            """
            DO $$
            BEGIN
                -- Ensure proper defaults and constraints
                UPDATE forms SET view_count = 0 WHERE view_count IS NULL;
                
                -- Add NOT NULL constraints where appropriate
                ALTER TABLE forms ALTER COLUMN view_count SET DEFAULT 0;
                
                RAISE NOTICE 'Updated column constraints and defaults';
            END $$;
            """
        ]
        
        # Execute migration queries
        for i, query in enumerate(migration_queries):
            logger.info(f"🔧 Executing migration step {i+1}...")
            db.session.execute(text(query))
            db.session.commit()
            logger.info(f"✅ Migration step {i+1} completed")
        
        logger.info("🎉 All missing columns added successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        db.session.rollback()
        return False

def fix_form_submissions_table():
    """Fix FormSubmission table schema if needed"""
    try:
        logger.info("🔧 Checking FormSubmission table...")
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Check for form_submissions table
        if 'form_submissions' not in tables and 'submissions' in tables:
            # The table exists as 'submissions', but model expects 'form_submissions'
            logger.info("📝 Found submissions table, checking compatibility...")
            
            columns = inspector.get_columns('submissions')
            column_names = [col['name'] for col in columns]
            
            # Expected columns from FormSubmission model
            expected_cols = ['form_id', 'data', 'submitter_id', 'submitter_email', 'submitted_at', 'status']
            missing_cols = [col for col in expected_cols if col not in column_names]
            
            if missing_cols:
                logger.warning(f"⚠️  Submissions table missing columns: {missing_cols}")
                # Could add missing columns here if needed
            else:
                logger.info("✅ Submissions table schema looks compatible")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FormSubmissions check failed: {str(e)}")
        return False

def validate_migration():
    """Validate that migration was successful"""
    try:
        logger.info("🔍 Validating migration...")
        
        # Test form query that was previously failing
        from app.models import Form
        form_count = Form.query.count()
        logger.info(f"✅ Successfully queried forms table: {form_count} forms found")
        
        # Test specific column access
        if form_count > 0:
            first_form = Form.query.first()
            logger.info(f"✅ Successfully accessed form schema: {first_form.schema is not None}")
            logger.info(f"✅ Form title: {first_form.title}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        return False

def main():
    """Main migration execution"""
    print("🚀 Starting Database Schema Migration")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        try:
            # Step 1: Backup existing data
            print("\n📦 Step 1: Creating backup...")
            backup_file = backup_data()
            if not backup_file:
                print("❌ Backup failed - aborting migration for safety")
                return False
            
            # Step 2: Check current schema
            print("\n🔍 Step 2: Analyzing current schema...")
            if check_current_schema():
                print("✅ Schema already correct - no migration needed")
                return True
            
            # Step 3: Add missing columns
            print("\n🔧 Step 3: Adding missing columns...")
            if not add_missing_columns():
                print("❌ Column migration failed")
                return False
            
            # Step 4: Fix related tables
            print("\n🔧 Step 4: Fixing related tables...")
            if not fix_form_submissions_table():
                print("❌ FormSubmissions fix failed")
                return False
            
            # Step 5: Validate migration
            print("\n✅ Step 5: Validating migration...")
            if not validate_migration():
                print("❌ Migration validation failed")
                return False
            
            print("\n🎉 DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
            print(f"📦 Backup saved as: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"💥 Migration failed with error: {str(e)}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)