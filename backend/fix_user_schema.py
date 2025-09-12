#!/usr/bin/env python3
"""
Fix User Schema Mismatch
This script fixes the mismatch between the User model and the existing Supabase database schema
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_user_schema():
    """Get the existing Supabase user schema"""
    try:
        import psycopg2
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return None
            
        print("🔗 Connecting to Supabase database...")
        
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Get users table schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        schema = {}
        for col in columns:
            col_name, data_type, nullable, default, max_length = col
            schema[col_name] = {
                'type': data_type,
                'nullable': nullable == 'YES',
                'default': default,
                'max_length': max_length
            }
        
        cur.close()
        conn.close()
        
        return schema
        
    except Exception as e:
        print(f"❌ Error getting schema: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_supabase_compatible_user_model():
    """Create a User model that's compatible with the existing Supabase schema"""
    
    model_code = '''"""
User Model Compatible with Supabase Schema
This model matches the existing Supabase database structure
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, ForeignKey, Integer, SmallInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from app import db

class User(db.Model):
    """User model compatible with existing Supabase schema"""
    __tablename__ = 'users'
    
    # Primary key - using the existing Supabase id field
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Supabase specific fields
    instance_id = Column(String(36), nullable=True)
    organization_id = Column(String(36), nullable=True)
    aud = Column(String(255), nullable=True)
    
    # Authentication fields
    email = Column(String(255), nullable=False, unique=True)
    encrypted_password = Column(String(255), nullable=True)  # Supabase uses this
    password_hash = Column(String(255), nullable=True)      # Our custom field
    
    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    username = Column(String(50), nullable=True, unique=True)
    phone = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    company = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, nullable=True, default=True)
    is_verified = Column(Boolean, nullable=True, default=False)
    is_super_admin = Column(Boolean, nullable=True, default=False)
    is_sso_user = Column(Boolean, nullable=False, default=False)
    is_anonymous = Column(Boolean, nullable=False, default=False)
    
    # Email verification
    email_confirmed_at = Column(DateTime, nullable=True)
    email_change = Column(String(255), nullable=True)
    email_change_token_new = Column(String(255), nullable=True)
    email_change_token_current = Column(String(255), nullable=True)
    email_change_sent_at = Column(DateTime, nullable=True)
    email_change_confirm_status = Column(SmallInteger, nullable=True, default=0)
    confirmation_token = Column(String(255), nullable=True)
    confirmation_sent_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Phone verification
    phone_confirmed_at = Column(DateTime, nullable=True)
    phone_change = Column(Text, nullable=True, default='')
    phone_change_token = Column(String(255), nullable=True, default='')
    phone_change_sent_at = Column(DateTime, nullable=True)
    
    # Password management
    password_changed_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Recovery and reauthentication
    recovery_token = Column(String(255), nullable=True)
    recovery_sent_at = Column(DateTime, nullable=True)
    reauthentication_token = Column(String(255), nullable=True, default='')
    reauthentication_sent_at = Column(DateTime, nullable=True)
    
    # Login tracking
    last_login_at = Column(DateTime, nullable=True)
    last_sign_in_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, nullable=True, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Account management
    invited_at = Column(DateTime, nullable=True)
    banned_until = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Preferences
    timezone = Column(String(50), nullable=True, default='UTC')
    language = Column(String(10), nullable=True, default='en')
    theme = Column(String(20), nullable=True, default='light')
    email_notifications = Column(Boolean, nullable=True, default=True)
    push_notifications = Column(Boolean, nullable=True, default=False)
    
    # Metadata
    raw_app_meta_data = Column(JSON, nullable=True)
    raw_user_meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Role (for backward compatibility)
    role = Column(String(255), nullable=True)
    
    # Relationships
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="creator", cascade="all, delete-orphan")
    form_submissions = relationship("FormSubmission", back_populates="submitter", cascade="all, delete-orphan")
    files = relationship("File", back_populates="uploader", cascade="all, delete-orphan")

    def set_password(self, password):
        """Set password hash - update both fields for compatibility"""
        self.password_hash = generate_password_hash(password)
        self.encrypted_password = generate_password_hash(password)

    def check_password(self, password):
        """Check password - try both fields"""
        if self.password_hash and check_password_hash(self.password_hash, password):
            return True
        if self.encrypted_password and check_password_hash(self.encrypted_password, password):
            return True
        return False
    
    def get_full_name(self):
        """Get full name from first and last name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username or self.email

    def update_last_login(self):
        """Update last login timestamp"""
        now = datetime.utcnow()
        self.last_login_at = now
        self.last_sign_in_at = now
        self.failed_login_attempts = 0  # Reset failed attempts on successful login

    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)

    def is_account_locked(self):
        """Check if account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'company': self.company,
            'job_title': self.job_title,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if include_sensitive:
            data.update({
                'is_sso_user': self.is_sso_user,
                'is_anonymous': self.is_anonymous,
                'failed_login_attempts': self.failed_login_attempts,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            })
        
        return data

    def __repr__(self):
        return f'<User {self.email}>'
'''
    
    return model_code

def backup_existing_model():
    """Backup the existing user model"""
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"user_models_backup_{timestamp}.py"
        
        shutil.copy("app/models/production/user_models.py", backup_path)
        print(f"✅ Existing model backed up to: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error backing up model: {e}")
        return False

def update_user_model():
    """Update the user model to match Supabase schema"""
    try:
        # Backup existing model
        if not backup_existing_model():
            return False
        
        # Create new model content
        new_model_content = create_supabase_compatible_user_model()
        
        # Write new model
        with open("app/models/production/user_models.py", "w") as f:
            f.write(new_model_content)
        
        print("✅ User model updated to match Supabase schema")
        return True
        
    except Exception as e:
        print(f"❌ Error updating model: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("FIXING USER SCHEMA MISMATCH")
    print("=" * 60)
    
    # Get current schema
    schema = get_supabase_user_schema()
    if not schema:
        print("❌ Could not get database schema")
        return
    
    print(f"\n📊 Found {len(schema)} columns in existing Supabase users table")
    
    # Update the model
    if update_user_model():
        print("\n✅ User model has been updated to match Supabase schema!")
        print("\n📝 Next steps:")
        print("   1. Test the application: python run.py")
        print("   2. If successful, you should be able to login/register")
        print("   3. The model now uses the existing Supabase columns")
    else:
        print("\n❌ Failed to update user model")

if __name__ == "__main__":
    main()
