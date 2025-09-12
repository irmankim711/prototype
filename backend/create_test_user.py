#!/usr/bin/env python3
"""
Script to create a test user with a known password for testing
"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_test_user():
    """Create a test user with a known password"""
    
    app = create_app()
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(email='test@example.com').first()
        
        if existing_user:
            print(f"🔍 Found existing user: {existing_user.email}")
            print(f"🔑 Current password hash: {existing_user.password_hash}")
            
            # Update password to a known value
            new_password = "testpass123"
            existing_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            print(f"✅ Updated password for {existing_user.email}")
            print(f"🔑 New password: {new_password}")
            print(f"🔐 New hash: {existing_user.password_hash}")
            
        else:
            print("🔍 No existing test user found, creating new one...")
            
            # Create new test user
            new_password = "testpass123"
            test_user = User(
                email='test@example.com',
                username='testuser',
                password_hash=generate_password_hash(new_password),
                first_name='Test',
                last_name='User',
                is_active=True
            )
            
            db.session.add(test_user)
            db.session.commit()
            
            print(f"✅ Created new test user: {test_user.email}")
            print(f"🔑 Password: {new_password}")
            print(f"🔐 Hash: {test_user.password_hash}")
        
        print("\n🎯 Test user ready for authentication testing!")
        print(f"📧 Email: test@example.com")
        print(f"🔑 Password: {new_password}")

if __name__ == "__main__":
    create_test_user()
