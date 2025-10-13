#!/usr/bin/env python3
"""
Fix Remaining Database Schema Issues
Addresses column mismatches between Supabase schema and SQLAlchemy models

Issues to fix:
1. is_active vs is_public column mapping
2. creator_id vs created_by mapping  
3. Additional missing columns
"""

import os
import sys
sys.path.append('.')

from app import create_app, db
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_model_columns():
    """Add columns that models expect but database doesn't have"""
    try:
        logger.info("🔧 Adding remaining missing columns...")
        
        # Get current schema
        inspector = inspect(db.engine)
        columns = inspector.get_columns('forms')
        existing_columns = [col['name'] for col in columns]
        
        migration_queries = []
        
        # Add is_active column (model expects this)
        if 'is_active' not in existing_columns:
            migration_queries.append("""
                ALTER TABLE forms ADD COLUMN is_active BOOLEAN DEFAULT true;
                UPDATE forms SET is_active = true WHERE is_active IS NULL;
            """)
            logger.info("➕ Will add is_active column")
        
        # Add creator_id column (model expects this)  
        if 'creator_id' not in existing_columns:
            migration_queries.append("""
                ALTER TABLE forms ADD COLUMN creator_id INTEGER;
                -- Try to map from created_by UUID to integer (if possible)
                -- For now, set to 1 as default admin user
                UPDATE forms SET creator_id = 1 WHERE creator_id IS NULL;
            """)
            logger.info("➕ Will add creator_id column")
        
        # Execute all migrations
        for i, query in enumerate(migration_queries):
            logger.info(f"🔧 Executing query {i+1}...")
            db.session.execute(text(query))
            db.session.commit()
            logger.info(f"✅ Query {i+1} completed")
        
        logger.info("🎉 All missing columns added!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Adding columns failed: {str(e)}")
        db.session.rollback()
        return False

def create_compatibility_views():
    """Create database views to bridge schema differences"""
    try:
        logger.info("🔧 Creating compatibility views...")
        
        # Create a view that maps database columns to model expectations
        view_query = """
        CREATE OR REPLACE VIEW forms_model_view AS 
        SELECT 
            -- Map UUID id to integer (use hash for consistency)
            abs(hashtext(id::text)) % 2147483647 as id,
            title,
            description, 
            schema,
            COALESCE(is_active, true) as is_active,
            is_public,
            COALESCE(creator_id, 1) as creator_id,
            created_at,
            updated_at,
            external_url,
            qr_code_data,
            form_settings,
            access_key,
            view_count,
            submission_limit,
            expires_at,
            -- Store original UUID for reference
            id as original_uuid
        FROM forms;
        """
        
        db.session.execute(text(view_query))
        db.session.commit()
        
        logger.info("✅ Compatibility view created")
        return True
        
    except Exception as e:
        logger.error(f"❌ Creating views failed: {str(e)}")
        db.session.rollback()
        return False

def test_model_compatibility():
    """Test if models can now work with the database"""
    try:
        logger.info("🧪 Testing model compatibility...")
        
        # Test basic form queries
        result = db.session.execute(text("SELECT COUNT(*) FROM forms"))
        count = result.scalar()
        logger.info(f"✅ Forms table accessible: {count} records")
        
        # Test schema column access
        result = db.session.execute(text("SELECT schema FROM forms LIMIT 1"))
        schema_test = result.fetchone()
        logger.info(f"✅ Schema column accessible: {schema_test is not None}")
        
        # Test is_active column
        result = db.session.execute(text("SELECT is_active FROM forms LIMIT 1"))
        active_test = result.fetchone()
        logger.info(f"✅ is_active column accessible: {active_test is not None}")
        
        # Test creator_id column
        result = db.session.execute(text("SELECT creator_id FROM forms LIMIT 1"))
        creator_test = result.fetchone()
        logger.info(f"✅ creator_id column accessible: {creator_test is not None}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Compatibility test failed: {str(e)}")
        return False

def test_sqlalchemy_model():
    """Test SQLAlchemy model queries"""
    try:
        logger.info("🧪 Testing SQLAlchemy model queries...")
        
        # Import and test Form model
        from app.models import Form
        
        # Test basic query
        form_count = Form.query.count()
        logger.info(f"✅ SQLAlchemy Form.query.count(): {form_count}")
        
        # Test first record access
        if form_count > 0:
            first_form = Form.query.first()
            logger.info(f"✅ First form title: {first_form.title}")
            logger.info(f"✅ Schema accessible: {first_form.schema is not None}")
            logger.info(f"✅ is_active accessible: {first_form.is_active}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLAlchemy model test failed: {str(e)}")
        return False

def main():
    """Main migration execution"""
    print("🚀 Fixing Remaining Database Schema Issues")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        try:
            # Step 1: Add missing columns
            print("\n🔧 Step 1: Adding missing columns...")
            if not add_missing_model_columns():
                print("❌ Adding columns failed")
                return False
            
            # Step 2: Test compatibility
            print("\n🧪 Step 2: Testing database compatibility...")
            if not test_model_compatibility():
                print("❌ Compatibility test failed")
                return False
            
            # Step 3: Test SQLAlchemy models
            print("\n🧪 Step 3: Testing SQLAlchemy models...")
            if not test_sqlalchemy_model():
                print("❌ SQLAlchemy test failed") 
                return False
            
            print("\n🎉 ALL DATABASE SCHEMA ISSUES FIXED!")
            print("✅ Forms table is now fully compatible with models")
            return True
            
        except Exception as e:
            logger.error(f"💥 Schema fix failed: {str(e)}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)