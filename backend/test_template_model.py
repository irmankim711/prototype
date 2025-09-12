#!/usr/bin/env python3
"""
Test the ReportTemplate model structure
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import create_app, db
from app.models import ReportTemplate

def test_model():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        print("🔍 ReportTemplate model columns:")
        for column in ReportTemplate.__table__.columns:
            print(f"  - {column.name}: {column.type}")
        
        print("\n🔍 Testing model creation...")
        
        # Try creating a simple template
        test_template = ReportTemplate(
            name="Test Template",
            description="Test description"
        )
        
        # Check if schema field exists
        if hasattr(test_template, 'schema'):
            print("✅ Schema field exists")
            test_template.schema = {'test': 'data'}
        else:
            print("❌ Schema field missing")
        
        try:
            db.session.add(test_template)
            db.session.commit()
            print("✅ Template created successfully")
            print(f"   ID: {test_template.id}")
            print(f"   Name: {test_template.name}")
            if hasattr(test_template, 'schema'):
                print(f"   Schema: {test_template.schema}")
        except Exception as e:
            print(f"❌ Error creating template: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    test_model()