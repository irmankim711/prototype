#!/usr/bin/env python3
"""
Create Test Data for Automation Testing
Creates a test form and submission to test the end-to-end automation
"""

from app import create_app, db
from app.models import Form, User, FormSubmission
from datetime import datetime
import json

def create_test_data():
    """Create test form and submission data"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Creating test data for automation testing...")
        
        # Create or get test user
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            user = User(
                email='test@example.com',
                username='testuser',
                password_hash='test_hash'
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created test user: {user.email}")
        else:
            print(f"✅ Using existing test user: {user.email}")
        
        # Create test form
        form = Form.query.filter_by(title='Test Automation Form').first()
        if not form:
            form = Form(
                title='Test Automation Form',
                description='Testing end-to-end automation workflow',
                schema=json.dumps([
                    {'name': 'name', 'type': 'text', 'required': True, 'label': 'Full Name'},
                    {'name': 'email', 'type': 'email', 'required': True, 'label': 'Email Address'},
                    {'name': 'age', 'type': 'number', 'required': False, 'label': 'Age'},
                    {'name': 'department', 'type': 'select', 'required': True, 'label': 'Department', 'options': ['IT', 'HR', 'Finance', 'Marketing']}
                ]),
                is_public=True,
                is_active=True,
                creator_id=user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(form)
            db.session.commit()
            print(f"✅ Created test form: {form.title} (ID: {form.id})")
        else:
            print(f"✅ Using existing test form: {form.title} (ID: {form.id})")
        
        # Create test submissions
        submissions_data = [
            {
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'age': 30,
                'department': 'IT'
            },
            {
                'name': 'Jane Smith',
                'email': 'jane.smith@example.com',
                'age': 28,
                'department': 'HR'
            },
            {
                'name': 'Bob Johnson',
                'email': 'bob.johnson@example.com',
                'age': 35,
                'department': 'Finance'
            }
        ]
        
        for i, data in enumerate(submissions_data):
            submission = FormSubmission(
                form_id=form.id,
                data=json.dumps(data),
                submitter_email=data['email'],
                submitted_at=datetime.utcnow(),
                status='completed'
            )
            db.session.add(submission)
        
        db.session.commit()
        print(f"✅ Created {len(submissions_data)} test submissions")
        
        print("\n🎯 Test data created successfully!")
        print(f"   Form ID: {form.id}")
        print(f"   User ID: {user.id}")
        print(f"   Submissions: {len(submissions_data)}")
        
        return form.id, user.id

if __name__ == '__main__':
    create_test_data()
