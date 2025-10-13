#!/usr/bin/env python3
"""
Script to create test forms in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Form, User
from datetime import datetime

def create_test_forms():
    """Create test forms in the database"""
    app = create_app()
    
    with app.app_context():
                # Create a test user if it doesn't exist
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(
                email='test@example.com',
                first_name='Test',
                last_name='User',
                is_active=True
            )
            test_user.set_password('testpassword123')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Created test user")
        else:
            print("✅ Test user already exists")
        
        # Create test forms
        test_forms = [
            {
                'title': 'Employee Satisfaction Survey',
                'description': 'Quarterly employee feedback and satisfaction survey',
                'schema': {
                    'fields': [
                        {
                            'id': 'name',
                            'label': 'Full Name',
                            'type': 'text',
                            'required': True,
                            'order': 1
                        },
                        {
                            'id': 'department',
                            'label': 'Department',
                            'type': 'select',
                            'required': True,
                            'options': ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance'],
                            'order': 2
                        },
                        {
                            'id': 'satisfaction',
                            'label': 'Job Satisfaction (1-10)',
                            'type': 'number',
                            'required': True,
                            'validation': {'min': 1, 'max': 10},
                            'order': 3
                        },
                        {
                            'id': 'feedback',
                            'label': 'Additional Feedback',
                            'type': 'textarea',
                            'required': False,
                            'order': 4
                        }
                    ]
                },
                'is_active': True,
                'is_public': True,
                'form_settings': {
                    'auto_generate_reports': True,
                    'report_schedule': 'weekly'
                }
            },
            {
                'title': 'Customer Feedback Form',
                'description': 'Customer experience and product feedback collection',
                'schema': {
                    'fields': [
                        {
                            'id': 'customer_name',
                            'label': 'Customer Name',
                            'type': 'text',
                            'required': True,
                            'order': 1
                        },
                        {
                            'id': 'product_rating',
                            'label': 'Product Rating (1-5)',
                            'type': 'number',
                            'required': True,
                            'validation': {'min': 1, 'max': 5},
                            'order': 2
                        },
                        {
                            'id': 'service_rating',
                            'label': 'Service Rating (1-5)',
                            'type': 'number',
                            'required': True,
                            'validation': {'min': 1, 'max': 5},
                            'order': 3
                        },
                        {
                            'id': 'recommendation',
                            'label': 'Would you recommend us?',
                            'type': 'radio',
                            'required': True,
                            'options': ['Yes', 'No', 'Maybe'],
                            'order': 4
                        },
                        {
                            'id': 'comments',
                            'label': 'Additional Comments',
                            'type': 'textarea',
                            'required': False,
                            'order': 5
                        }
                    ]
                },
                'is_active': True,
                'is_public': True,
                'form_settings': {
                    'auto_generate_reports': True,
                    'report_schedule': 'daily'
                }
            },
            {
                'title': 'IT Support Request',
                'description': 'Technical support and issue reporting form',
                'schema': {
                    'fields': [
                        {
                            'id': 'employee_name',
                            'label': 'Employee Name',
                            'type': 'text',
                            'required': True,
                            'order': 1
                        },
                        {
                            'id': 'issue_type',
                            'label': 'Issue Type',
                            'type': 'select',
                            'required': True,
                            'options': ['Hardware', 'Software', 'Network', 'Access', 'Other'],
                            'order': 2
                        },
                        {
                            'id': 'priority',
                            'label': 'Priority Level',
                            'type': 'radio',
                            'required': True,
                            'options': ['Low', 'Medium', 'High', 'Critical'],
                            'order': 3
                        },
                        {
                            'id': 'description',
                            'label': 'Issue Description',
                            'type': 'textarea',
                            'required': True,
                            'order': 4
                        },
                        {
                            'id': 'contact_preference',
                            'label': 'Preferred Contact Method',
                            'type': 'checkbox',
                            'required': False,
                            'options': ['Email', 'Phone', 'Teams'],
                            'order': 5
                        }
                    ]
                },
                'is_active': True,
                'is_public': True,
                'form_settings': {
                    'auto_generate_reports': False
                }
            },
            {
                'title': 'Event Registration',
                'description': 'Conference and workshop registration form',
                'schema': {
                    'fields': [
                        {
                            'id': 'attendee_name',
                            'label': 'Attendee Name',
                            'type': 'text',
                            'required': True,
                            'order': 1
                        },
                        {
                            'id': 'email',
                            'label': 'Email Address',
                            'type': 'email',
                            'required': True,
                            'order': 2
                        },
                        {
                            'id': 'company',
                            'label': 'Company',
                            'type': 'text',
                            'required': False,
                            'order': 3
                        },
                        {
                            'id': 'session_preferences',
                            'label': 'Session Preferences',
                            'type': 'checkbox',
                            'required': False,
                            'options': ['Keynote', 'Technical Sessions', 'Networking', 'Workshops'],
                            'order': 4
                        },
                        {
                            'id': 'dietary_restrictions',
                            'label': 'Dietary Restrictions',
                            'type': 'textarea',
                            'required': False,
                            'order': 5
                        }
                    ]
                },
                'is_active': True,
                'is_public': True,
                'form_settings': {
                    'auto_generate_reports': True,
                    'report_schedule': 'monthly'
                }
            }
        ]
        
        # Create forms
        created_forms = []
        for form_data in test_forms:
            # Check if form already exists
            existing_form = Form.query.filter_by(title=form_data['title']).first()
            if existing_form:
                print(f"⚠️ Form '{form_data['title']}' already exists")
                continue
            
            form = Form(
                title=form_data['title'],
                description=form_data['description'],
                schema=form_data['schema'],
                is_active=form_data['is_active'],
                is_public=form_data['is_public'],
                creator_id=test_user.id,
                form_settings=form_data['form_settings'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(form)
            created_forms.append(form)
            print(f"✅ Created form: {form_data['title']}")
        
        db.session.commit()
        print(f"🎉 Successfully created {len(created_forms)} test forms")
        
        # Print form IDs for testing
        print("\n📋 Form IDs for testing:")
        for form in Form.query.filter_by(creator_id=test_user.id).all():
            print(f"  - {form.title}: ID {form.id}")

if __name__ == "__main__":
    create_test_forms() 