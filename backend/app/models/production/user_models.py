"""
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
    """User model compatible with existing database schema"""
    __tablename__ = 'user'
    
    # Primary key - using Integer as per database schema
    id = Column(Integer, primary_key=True)
    
    # Basic authentication fields
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Basic profile fields
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    username = Column(String(50), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    company = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships - Commented out to avoid foreign key issues during testing
    # tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    # sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    # forms = relationship("Form", back_populates="creator", cascade="all, delete-orphan")
    # form_submissions = relationship("FormSubmission", back_populates="submitter", cascade="all, delete-orphan")
    # files = relationship("File", back_populates="uploader", cascade="all, delete-orphan")

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
        self.last_login = datetime.utcnow()

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        return data

    def __repr__(self):
        return f'<User {self.email}>'


class UserToken(db.Model):
    """Real OAuth token storage - NO MOCK DATA"""
    __tablename__ = 'user_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)  # Updated to match User.id type
    
    # Platform information
    platform = Column(String(50), nullable=False)  # google, microsoft, local
    platform_user_id = Column(String(255))  # User ID on the platform
    
    # Token data (encrypted)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_type = Column(String(20), default='Bearer')
    
    # Token metadata
    scopes = Column(JSON)  # Granted scopes
    expires_at = Column(DateTime)
    issued_at = Column(DateTime, default=datetime.utcnow)
    
    # Security
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime)
    revoke_reason = Column(String(100))
    
    # Usage tracking
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    # Relationships - Commented out to avoid circular dependency issues
    # user = relationship("User", back_populates="tokens")

    def is_expired(self):
        """Check if token is expired"""
        if self.expires_at:
            return datetime.utcnow() >= self.expires_at
        return False

    def is_valid(self):
        """Check if token is valid"""
        return self.is_active and not self.is_expired() and not self.revoked_at

    def revoke(self, reason="user_request"):
        """Revoke the token"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revoke_reason = reason

    def update_usage(self):
        """Update token usage tracking"""
        self.last_used = datetime.utcnow()
        self.usage_count = (self.usage_count or 0) + 1

    def to_dict(self, include_tokens=False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'platform': self.platform,
            'platform_user_id': self.platform_user_id,
            'token_type': self.token_type,
            'scopes': self.scopes,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count
        }
        
        if include_tokens:
            # Only include for admin or debugging purposes
            data.update({
                'access_token': self.access_token[:20] + '...' if self.access_token else None,
                'has_refresh_token': bool(self.refresh_token)
            })
        
        return data


class UserSession(db.Model):
    """User session tracking - NO MOCK DATA"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)  # Updated to match User.id type
    session_token = Column(String(255), unique=True, nullable=False)
    
    # Session metadata
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    browser = Column(String(100))
    operating_system = Column(String(100))
    device_type = Column(String(50))  # desktop, mobile, tablet
    
    # Session status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    # Security tracking
    login_method = Column(String(50))  # password, google, microsoft
    is_suspicious = Column(Boolean, default=False)
    security_flags = Column(JSON)  # Security-related flags
    
    # Relationship - Commented out to avoid circular dependency issues
    # user = relationship("User", back_populates="sessions")
    
    def is_expired(self):
        """Check if session is expired"""
        if self.expires_at:
            return datetime.utcnow() >= self.expires_at
        return False

    def is_valid(self):
        """Check if session is valid"""
        return self.is_active and not self.is_expired() and not self.ended_at

    def end_session(self):
        """End the session"""
        self.is_active = False
        self.ended_at = datetime.utcnow()

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'session_token': self.session_token[:10] + '...' if self.session_token else None,
            'ip_address': self.ip_address,
            'browser': self.browser,
            'operating_system': self.operating_system,
            'device_type': self.device_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'login_method': self.login_method,
            'is_suspicious': self.is_suspicious,
            'is_valid': self.is_valid()
        }
