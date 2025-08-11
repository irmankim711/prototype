#!/usr/bin/env python3
"""
Script to create sample forms and submissions for testing the submissions page
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, User, Form, FormSubmission
from datetime import datetime, timedelta
import json
import random

def create_sample_data():
    app = create_app()
    
    with app.app_context():
        # Check if we have users
        users = User.query.all()
        if not users:
            print("No users found. Please create a user account first.")
            return
        
        user = users[0]  # Use first user
        print(f"Using user: {user.email}")
        
        # Create sample forms if they don't exist
        existing_forms = Form.query.filter_by(creator_id=user.id).all()
        if len(existing_forms) < 2:
            print("Creating sample forms...")
            
            # Form 1: Contact Form
            contact_form_schema = {
                "fields": [
                    {
                        "id": "name",
                        "label": "Full Name",
                        "type": "text",
                        "required": True,
                        "order": 1
                    },
                    {
                        "id": "email",
                        "label": "Email Address",
                        "type": "email",
                        "required": True,
                        "order": 2
                    },
                    {
                        "id": "phone",
                        "label": "Phone Number",
                        "type": "phone",
                        "required": False,
                        "order": 3
                    },
                    {
                        "id": "message",
                        "label": "Message",
                        "type": "textarea",
                        "required": True,
                        "order": 4
                    }
                ]
            }
            
            contact_form = Form(
                title="Contact Us Form",
                description="Get in touch with our team",
                schema=contact_form_schema,
                is_active=True,
                is_public=True,
                creator_id=user.id
            )
            db.session.add(contact_form)
            
            # Form 2: Feedback Form
            feedback_form_schema = {
                "fields": [
                    {
                        "id": "name",
                        "label": "Your Name",
                        "type": "text",
                        "required": True,
                        "order": 1
                    },
                    {
                        "id": "email",
                        "label": "Email",
                        "type": "email",
                        "required": True,
                        "order": 2
                    },
                    {
                        "id": "rating",
                        "label": "Overall Rating",
                        "type": "rating",
                        "required": True,
                        "order": 3
                    },
                    {
                        "id": "experience",
                        "label": "How was your experience?",
                        "type": "select",
                        "required": True,
                        "options": ["Excellent", "Good", "Average", "Poor"],
                        "order": 4
                    },
                    {
                        "id": "feedback",
                        "label": "Additional Feedback",
                        "type": "textarea",
                        "required": False,
                        "order": 5
                    }
                ]
            }
            
            feedback_form = Form(
                title="Customer Feedback Form",
                description="Help us improve our service",
                schema=feedback_form_schema,
                is_active=True,
                is_public=True,
                creator_id=user.id
            )
            db.session.add(feedback_form)
            db.session.commit()
            print("Sample forms created!")
        
        # Get forms for creating submissions
        forms = Form.query.filter_by(creator_id=user.id).all()
        if not forms:
            print("No forms found to create submissions")
            return
        
        print(f"Found {len(forms)} forms")
        
        # Create sample submissions
        existing_submissions = FormSubmission.query.join(Form).filter(Form.creator_id == user.id).count()
        if existing_submissions < 10:
            print("Creating sample submissions...")
            
            # Sample names and emails
            sample_data = [
                {"name": "Alice Johnson", "email": "alice.johnson@email.com"},
                {"name": "Bob Smith", "email": "bob.smith@email.com"},
                {"name": "Charlie Brown", "email": "charlie.brown@email.com"},
                {"name": "Diana Ross", "email": "diana.ross@email.com"},
                {"name": "Eve Williams", "email": "eve.williams@email.com"},
                {"name": "Frank Miller", "email": "frank.miller@email.com"},
                {"name": "Grace Chen", "email": "grace.chen@email.com"},
                {"name": "Henry Davis", "email": "henry.davis@email.com"},
                {"name": "Ivy Taylor", "email": "ivy.taylor@email.com"},
                {"name": "Jack Wilson", "email": "jack.wilson@email.com"},
            ]
            
            for i, person in enumerate(sample_data):
                form = forms[i % len(forms)]  # Rotate through forms
                
                # Create submission data based on form schema
                submission_data = {}
                for field in form.schema.get('fields', []):
                    field_id = field['id']
                    field_type = field['type']
                    
                    if field_id == 'name':
                        submission_data[field_id] = person['name']
                    elif field_id == 'email':
                        submission_data[field_id] = person['email']
                    elif field_id == 'phone':
                        submission_data[field_id] = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                    elif field_id == 'message':
                        messages = [
                            "Hello, I have a question about your services.",
                            "I'm interested in learning more about your products.",
                            "Could you please provide more information?",
                            "I would like to schedule a consultation.",
                            "Thank you for your excellent service!"
                        ]
                        submission_data[field_id] = random.choice(messages)
                    elif field_id == 'rating':
                        submission_data[field_id] = random.randint(3, 5)
                    elif field_id == 'experience':
                        experiences = ["Excellent", "Good", "Average"]
                        submission_data[field_id] = random.choice(experiences)
                    elif field_id == 'feedback':
                        feedbacks = [
                            "Great service, very satisfied!",
                            "Could improve response time.",
                            "Excellent customer support.",
                            "Very professional team.",
                            "Highly recommend to others."
                        ]
                        submission_data[field_id] = random.choice(feedbacks)
                
                # Create submission with random date in the last 30 days
                submission_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                
                submission = FormSubmission(
                    form_id=form.id,
                    data=submission_data,
                    submitter_email=person['email'],
                    submitted_at=submission_date,
                    status=random.choice(['submitted', 'reviewed', 'approved'])
                )
                
                db.session.add(submission)
            
            db.session.commit()
            print("Sample submissions created!")
        
        # Show statistics
        total_forms = Form.query.filter_by(creator_id=user.id).count()
        total_submissions = FormSubmission.query.join(Form).filter(Form.creator_id == user.id).count()
        
        print(f"\nDatabase Statistics:")
        print(f"Total Forms: {total_forms}")
        print(f"Total Submissions: {total_submissions}")
        
        # Show forms and their submissions
        for form in forms:
            form_submissions = FormSubmission.query.filter_by(form_id=form.id).count()
            print(f"- {form.title}: {form_submissions} submissions")

if __name__ == "__main__":
    create_sample_data()
