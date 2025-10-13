#!/usr/bin/env python3
"""
Create a simple test user for login testing using production models
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def create_test_user():
    """Create a test user for login testing"""
    
    print("=" * 50)
    print("CREATE TEST USER")
    print("=" * 50)
    
    try:
        # Import the app factory
        from app import create_app
        
        # Create app with production config
        app = create_app('production')
        
        with app.app_context():
            try:
                # Import production models
                from app.models import User
                
                # Check if test user already exists
                test_user = User.query.filter_by(email='test@example.com').first()
                
                if test_user:
                    print(f"✅ Test user already exists:")
                    print(f"   Email: {test_user.email}")
                    print(f"   Username: {test_user.username}")
                    print(f"   ID: {test_user.id}")
                    return test_user
                
                # Create test user
                print("🔨 Creating test user...")
                
                test_user = User(
                    email='test@example.com',
                    username='testuser',
                    first_name='Test',
                    last_name='User',
                    is_active=True,
                    is_verified=True
                )
                
                # Set password
                test_user.set_password('testpassword123')
                
                # Add to database
                from app import db
                db.session.add(test_user)
                db.session.commit()
                
                print("✅ Test user created successfully!")
                print(f"   Email: {test_user.email}")
                print(f"   Username: {test_user.username}")
                print(f"   Password: testpassword123")
                print(f"   ID: {test_user.id}")
                
                return test_user
                
            except Exception as e:
                print(f"❌ Error creating test user: {e}")
                import traceback
                traceback.print_exc()
                return None
                
    except Exception as e:
        print(f"❌ Error creating app: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_test_user()
