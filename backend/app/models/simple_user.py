"""
Simplified User model that matches the actual Supabase database structure
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from app import db

class SimpleUser(db.Model):
    """Simplified user model that matches the actual Supabase database"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Preferences
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    theme = Column(String(20), default='light')
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=False)
    
    # Relationships
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password"""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def get_full_name(self):
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username or self.email

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()
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
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login_at.isoformat() if self.last_login_at else None,
            'timezone': self.timezone,
            'language': self.language,
            'theme': self.theme,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_account_locked(),
                'locked_until': self.locked_until.isoformat() if self.locked_until else None
            })
        
        return data

    def __repr__(self):
        return f'<SimpleUser {self.email}>'
