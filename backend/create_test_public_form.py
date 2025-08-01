#!/usr/bin/env python3
"""
Quick script to create a test public form for testing the public forms page
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app import create_app
from app.models import db, Form

def create_test_public_form():
    """Create a sample public form for testing"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Sample form fields
            sample_fields = [
                {
                    "id": "field_1",
                    "type": "text",
                    "label": "Full Name",
                    "placeholder": "Enter your full name",
                    "required": True,
                    "validation": {
                        "required": True,
                        "minLength": 2
                    }
                },
                {
                    "id": "field_2", 
                    "type": "email",
                    "label": "Email Address",
                    "placeholder": "Enter your email",
                    "required": True,
                    "validation": {
                        "required": True
                    }
                },
                {
                    "id": "field_3",
                    "type": "textarea", 
                    "label": "Feedback",
                    "placeholder": "Please share your feedback",
                    "required": False,
                    "validation": {
                        "maxLength": 500
                    }
                },
                {
                    "id": "field_4",
                    "type": "radio",
                    "label": "How did you hear about us?",
                    "required": True,
                    "options": [
                        {"value": "google", "label": "Google Search"},
                        {"value": "social", "label": "Social Media"},
                        {"value": "friend", "label": "Friend/Family"},
                        {"value": "other", "label": "Other"}
                    ]
                }
            ]
            
            # Create the form
            new_form = Form(
                title="Customer Feedback Survey",
                description="Help us improve our services by sharing your valuable feedback. This survey takes only 2-3 minutes to complete.",
                schema=sample_fields,  # Use schema instead of fields
                is_public=True,
                is_active=True,
                creator_id=1  # Default admin user
            )
            
            db.session.add(new_form)
            db.session.commit()
            
            # Create an external form
            external_form = Form(
                title="Google Forms Survey",
                description="This is an external survey hosted on Google Forms. Click to access the form in a new tab.",
                external_url="https://forms.google.com/",
                is_public=False,  # External forms don't need to be marked as public
                is_active=True,
                creator_id=1
            )
            
            db.session.add(external_form)
            db.session.commit()
            
            print("✅ Successfully created test public form!")
            print(f"Form ID: {new_form.id}")
            print(f"Title: {new_form.title}")
            print(f"Public: {new_form.is_public}")
            print(f"Active: {new_form.is_active}")
            print(f"Fields: {len(sample_fields)}")
            
            print("\n✅ Successfully created test external form!")
            print(f"Form ID: {external_form.id}")
            print(f"Title: {external_form.title}")
            print(f"External URL: {external_form.external_url}")
            print(f"Active: {external_form.is_active}")
            
            return new_form
            
        except Exception as e:
            print(f"❌ Error creating test form: {e}")
            db.session.rollback()
            return None

if __name__ == "__main__":
    print("Creating test public form...")
    create_test_public_form()
