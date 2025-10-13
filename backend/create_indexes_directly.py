#!/usr/bin/env python3
"""
Direct Index Creation Script
Creates strategic database indexes directly using SQL commands.
"""

from app import create_app, db
import sqlalchemy as sa

def create_indexes_directly():
    """Create strategic indexes directly using SQL commands."""
    app = create_app()
    with app.app_context():
        # List of indexes to create
        indexes_to_create = [
            # Forms table indexes
            "CREATE INDEX IF NOT EXISTS idx_forms_creator_id ON forms(creator_id)",
            "CREATE INDEX IF NOT EXISTS idx_forms_is_active ON forms(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_forms_is_public ON forms(is_public)",
            "CREATE INDEX IF NOT EXISTS idx_forms_created_at ON forms(created_at)",
            
            # Form submissions table indexes
            "CREATE INDEX IF NOT EXISTS idx_form_submissions_form_id ON form_submissions(form_id)",
            "CREATE INDEX IF NOT EXISTS idx_form_submissions_submitted_at ON form_submissions(submitted_at)",
            "CREATE INDEX IF NOT EXISTS idx_form_submissions_status ON form_submissions(status)",
            "CREATE INDEX IF NOT EXISTS idx_form_submissions_submitter_id ON form_submissions(submitter_id)",
            "CREATE INDEX IF NOT EXISTS idx_form_submissions_form_submitted ON form_submissions(form_id, submitted_at)",
            
            # Reports table indexes
            "CREATE INDEX IF NOT EXISTS idx_reports_created_by ON reports(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_reports_generation_status ON reports(generation_status)",
            "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_reports_template_id ON reports(template_id)",
            "CREATE INDEX IF NOT EXISTS idx_reports_user_status ON reports(created_by, generation_status)",
            
            # User table indexes (try both 'user' and 'users' table names)
            "CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)",
            "CREATE INDEX IF NOT EXISTS idx_user_role ON user(role)",
            "CREATE INDEX IF NOT EXISTS idx_user_is_active ON user(is_active)",
        ]
        
        print("Creating strategic database indexes...")
        
        for index_sql in indexes_to_create:
            try:
                with db.engine.connect() as connection:
                    connection.execute(sa.text(index_sql))
                    connection.commit()
                print(f"✅ Created: {index_sql}")
            except Exception as e:
                print(f"⚠️ Skipped: {index_sql} - {str(e)}")
        
        print("\n🎉 Index creation completed!")
        
        # Verify indexes were created
        print("\nVerifying created indexes...")
        inspector = sa.inspect(db.engine)
        
        for table in ['forms', 'form_submissions', 'reports', 'user']:
            try:
                indexes = inspector.get_indexes(table)
                if indexes:
                    print(f"\n{table} indexes:")
                    for idx in indexes:
                        print(f"  - {idx['name']}: {idx['column_names']}")
                else:
                    print(f"\n{table}: No indexes found")
            except Exception as e:
                print(f"\n{table}: Error checking indexes - {str(e)}")

if __name__ == '__main__':
    create_indexes_directly()