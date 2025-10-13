#!/usr/bin/env python3
"""
Create a test user for Firebase authentication testing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.production.user_models import User
from app.models.production.permissions import UserRole
from datetime import datetime

def create_test_user():
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        test_email = "test@example.com"
        existing_user = User.query.filter_by(email=test_email).first()
        
        if existing_user:
            print(f"✅ Test user already exists: {existing_user.email} (ID: {existing_user.id})")
            return existing_user
        
        # Create new test user
        test_user = User(
            email=test_email,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_active=True,
            role=UserRole.USER,
            created_at=datetime.utcnow()
        )
        
        # Set a simple password
        test_user.set_password("password123")
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        print(f"   Password: password123")
        print(f"   You can use this to test Firebase authentication")
        
        return test_user

if __name__ == "__main__":
    create_test_user()