"""
User and Authentication Models for production deployment
NO MOCK DATA - Real user management and OAuth tokens
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from app import db

class User(db.Model):
    """Real user management - NO MOCK DATA"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(255))
    phone = Column(String(20))
    organization = Column(String(255))
    position = Column(String(255))
    department = Column(String(255))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    email_verified_at = Column(DateTime)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    email_verification_token = Column(String(255))
    
    # Preferences
    preferences = Column(JSON)  # User preferences and settings
    notification_settings = Column(JSON)  # Notification preferences
    
    # Relationships
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def update_full_name(self):
        """Update full name from first and last name"""
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        elif self.first_name:
            self.full_name = self.first_name
        elif self.last_name:
            self.full_name = self.last_name

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0  # Reset failed attempts on successful login

    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
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
            'uuid': self.uuid,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'organization': self.organization,
            'position': self.position,
            'department': self.department,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.preferences,
            'notification_settings': self.notification_settings
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_account_locked(),
                'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None
            })
        
        return data

class UserToken(db.Model):
    """Real OAuth token storage - NO MOCK DATA"""
    __tablename__ = 'user_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
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
    
    # Relationships
    user = relationship("User", back_populates="tokens")

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
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
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
