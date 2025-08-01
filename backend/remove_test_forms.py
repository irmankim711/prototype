#!/usr/bin/env python3
"""
Script to remove the first 3 test forms from the database
"""

import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app import create_app
from app.models import db, Form

def remove_test_forms():
    """Remove the first 3 test forms"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get the first 3 forms
            forms_to_delete = Form.query.order_by(Form.id).limit(3).all()
            
            if not forms_to_delete:
                print("❌ No forms found to delete")
                return
            
            print(f"Found {len(forms_to_delete)} forms to delete:")
            for form in forms_to_delete:
                print(f"  - ID: {form.id}, Title: {form.title}")
            
            # Confirm deletion
            print("\n🗑️  Deleting forms...")
            
            # Delete forms by ID to avoid cascade issues
            form_ids = [form.id for form in forms_to_delete]
            
            # Use raw SQL to delete
            for form_id in form_ids:
                db.session.execute(db.text("DELETE FROM form WHERE id = :id"), {"id": form_id})
            
            db.session.commit()
            
            print("✅ Successfully deleted all test forms!")
            
            # Verify deletion
            remaining_count = Form.query.count()
            print(f"📊 Remaining forms in database: {remaining_count}")
            
        except Exception as e:
            print(f"❌ Error deleting forms: {e}")
            db.session.rollback()

if __name__ == "__main__":
    print("Removing test forms...")
    remove_test_forms()
