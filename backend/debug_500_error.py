#!/usr/bin/env python3
"""
Debug script to identify the 500 error in the forms API
"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Load environment variables
load_dotenv()

def debug_forms_endpoint():
    """Debug the forms endpoint to identify 500 error"""
    
    print("=" * 60)
    print("🔍 DEBUGGING FORMS API 500 ERROR")
    print("=" * 60)
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')
    if 'postgresql://' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace(
            'postgresql://', 'postgresql+psycopg2://', 1
        )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    # Import models
    try:
        from app.models import User, Form, FormSubmission
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False
    
    with app.app_context():
        try:
            # 1. Check database connection
            print("\n1️⃣ Testing database connection...")
            result = db.session.execute(db.text("SELECT 1"))
            print("✅ Database connection successful")
            
            # 2. Check if tables exist
            print("\n2️⃣ Checking if tables exist...")
            tables = db.session.execute(db.text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)).fetchall()
            
            table_names = [row[0] for row in tables]
            print(f"📋 Found {len(table_names)} tables:")
            for table in table_names:
                print(f"   - {table}")
            
            required_tables = ['user', 'form', 'form_submission']
            missing_tables = [t for t in required_tables if t not in table_names]
            if missing_tables:
                print(f"⚠️  Missing required tables: {missing_tables}")
                return False
            
            # 3. Check for users
            print("\n3️⃣ Checking users...")
            user_count = User.query.count()
            print(f"👥 Found {user_count} users")
            
            if user_count == 0:
                print("⚠️  No users found - creating test user...")
                test_user = User(
                    email="test@example.com",
                    username="testuser",
                    first_name="Test",
                    last_name="User"
                )
                test_user.set_password("password123")
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created: test@example.com / password123")
            else:
                users = User.query.all()
                for user in users:
                    print(f"   - {user.email} (ID: {user.id})")
            
            # 4. Check forms
            print("\n4️⃣ Checking forms...")
            form_count = Form.query.count()
            print(f"📝 Found {form_count} forms")
            
            if form_count == 0:
                print("⚠️  No forms found - creating test form...")
                test_user = User.query.first()
                if test_user:
                    test_form = Form(
                        title="Test Form",
                        description="A test form for debugging",
                        schema={
                            "fields": [
                                {
                                    "id": "field_1",
                                    "type": "text",
                                    "label": "Your Name",
                                    "required": True,
                                    "order": 0
                                }
                            ]
                        },
                        is_public=True,
                        is_active=True,
                        creator_id=test_user.id
                    )
                    db.session.add(test_form)
                    db.session.commit()
                    print("✅ Test form created")
            else:
                forms = Form.query.all()
                for form in forms:
                    print(f"   - {form.title} (ID: {form.id}, Public: {form.is_public}, Active: {form.is_active})")
            
            # 5. Test the actual query from the API
            print("\n5️⃣ Testing public forms query...")
            public_forms = Form.query.filter_by(is_public=True, is_active=True).all()
            print(f"🌐 Found {len(public_forms)} public active forms")
            
            # 6. Test form data serialization
            print("\n6️⃣ Testing form data serialization...")
            for form in public_forms:
                try:
                    # Test the same logic as in the API
                    creator_name = 'System'
                    if form.creator:
                        creator_name = getattr(form.creator, 'username', None) or \
                                     getattr(form.creator, 'full_name', None) or \
                                     'Unknown'
                    
                    submission_count = FormSubmission.query.filter_by(form_id=form.id).count()
                    
                    field_count = 0
                    if form.schema and isinstance(form.schema, dict):
                        fields = form.schema.get('fields', [])
                        field_count = len(fields) if isinstance(fields, list) else 0
                    
                    form_data = {
                        'id': form.id,
                        'title': form.title or 'Untitled Form',
                        'description': form.description or '',
                        'created_at': form.created_at.isoformat() if form.created_at else None,
                        'updated_at': form.updated_at.isoformat() if form.updated_at else None,
                        'creator_name': creator_name,
                        'submission_count': submission_count,
                        'field_count': field_count,
                        'has_external_url': bool(form.external_url),
                        'external_url': form.external_url,
                        'is_public': form.is_public,
                        'is_active': form.is_active,
                        'view_count': getattr(form, 'view_count', 0) or 0
                    }
                    
                    print(f"✅ Form {form.id} serialized successfully")
                    
                except Exception as e:
                    print(f"❌ Error serializing form {form.id}: {e}")
                    print(f"   Form details: title={form.title}, creator_id={form.creator_id}")
                    return False
            
            print("\n✅ All tests passed! The API should work correctly.")
            print("🔧 Try restarting the Flask server and test again.")
            return True
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = debug_forms_endpoint()
    if success:
        print("\n🎉 Debugging completed successfully!")
    else:
        print("\n💥 Issues found - check the output above for details.")
        sys.exit(1)
