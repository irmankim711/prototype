"""
Simple Database Verification Script
Checks if templates table exists and shows current templates
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.template_models import Template

def verify_database():
    """Verify database setup and show templates"""
    print("\n" + "="*60)
    print("  DATABASE VERIFICATION - Template Models")
    print("="*60)

    app = create_app()

    with app.app_context():
        try:
            # Check if table exists
            print("\n✓ Checking database connection...")
            db.engine.connect()
            print("  ✅ Database connected successfully")

            # Check if templates table exists
            print("\n✓ Checking templates table...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            if 'templates' in tables:
                print("  ✅ 'templates' table exists")

                # Get columns
                columns = inspector.get_columns('templates')
                print(f"\n  Table has {len(columns)} columns:")
                for col in columns:
                    print(f"    - {col['name']}: {col['type']}")

            else:
                print("  ⚠️  'templates' table does NOT exist")
                print("  Creating tables...")
                db.create_all()
                print("  ✅ Tables created")

            # Query existing templates
            print("\n✓ Querying existing templates...")
            templates = Template.query.all()

            if templates:
                print(f"  ✅ Found {len(templates)} templates:")
                for template in templates:
                    print(f"\n    ID: {template.id}")
                    print(f"    Name: {template.name}")
                    print(f"    Type: {template.template_type}")
                    print(f"    Category: {template.category}")
                    print(f"    Active: {template.is_active}")
                    print(f"    Created: {template.created_at}")
            else:
                print("  ℹ️  No templates found in database")
                print("  This is normal for a fresh installation")

            # Test template creation
            print("\n✓ Testing template creation...")
            test_template = Template(
                name="Database Verification Test Template",
                description="Created by verify_template_db.py",
                category="test",
                template_type="jinja2",
                template_content="<h1>Test Template</h1>",
                created_by=1  # Assuming user ID 1 exists
            )

            db.session.add(test_template)
            db.session.commit()

            print(f"  ✅ Test template created with ID: {test_template.id}")

            # Clean up test template
            db.session.delete(test_template)
            db.session.commit()
            print("  ✅ Test template cleaned up")

            print("\n" + "="*60)
            print("  ✅ ALL CHECKS PASSED - Database is ready!")
            print("="*60 + "\n")

            return True

        except Exception as e:
            print(f"\n  ❌ ERROR: {str(e)}")
            import traceback
            print("\n" + traceback.format_exc())
            print("\n" + "="*60)
            print("  ❌ VERIFICATION FAILED")
            print("="*60 + "\n")
            return False


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
