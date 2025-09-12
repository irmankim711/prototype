"""
Form Models for production deployment
NO MOCK DATA - Real form management and submissions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app import db

class Form(db.Model):
    """Real form model for dynamic form creation and management - NO MOCK DATA"""
    __tablename__ = 'forms'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    schema = Column(JSON)  # Form structure definition
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Enhanced form builder fields
    external_url = Column(String(500))  # External URL for form sharing
    qr_code_data = Column(Text)  # Base64 encoded QR code
    form_settings = Column(JSON)  # Additional form settings (themes, notifications, etc.)
    access_key = Column(String(100))  # Unique access key for public forms
    view_count = Column(Integer, default=0)  # Track form views
    submission_limit = Column(Integer)  # Optional submission limit
    expires_at = Column(DateTime)  # Optional expiration date
    
    # Relationships - Commented out to avoid circular dependency issues
    submissions = relationship("FormSubmission", back_populates="form", cascade="all, delete-orphan")
    # creator = relationship("User", back_populates="forms")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'schema': self.schema,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'external_url': self.external_url,
            'access_key': self.access_key,
            'view_count': self.view_count,
            'submission_limit': self.submission_limit,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'submission_count': len(self.submissions) if self.submissions else 0
        }

class FormSubmission(db.Model):
    """Real form submission model for storing user form responses - NO MOCK DATA"""
    __tablename__ = 'form_submissions'
    
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    data = Column(JSON)  # Submitted form data
    submitter_id = Column(Integer, ForeignKey('user.id'))
    submitter_email = Column(String(120))  # For anonymous submissions
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='submitted')  # submitted, reviewed, approved, rejected
    
    # Enhanced submission tracking
    ip_address = Column(String(45))  # IPv4/IPv6 support
    user_agent = Column(Text)
    submission_source = Column(String(50), default='web')  # web, qr_code, api, mobile
    location_data = Column(JSON)  # Optional location information
    processing_notes = Column(Text)  # Admin notes for processing
    
    # Relationships - Commented out to avoid circular dependency issues
    form = relationship("Form", back_populates="submissions")
    # submitter = relationship("User", back_populates="form_submissions")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'form_id': self.form_id,
            'data': self.data,
            'submitter_id': self.submitter_id,
            'submitter_email': self.submitter_email,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'status': self.status,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'submission_source': self.submission_source,
            'location_data': self.location_data,
            'processing_notes': self.processing_notes
        }

class FormQRCode(db.Model):
    """Real QR Code model for form sharing and analytics - NO MOCK DATA"""
    __tablename__ = 'form_qr_codes'
    
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    qr_code_data = Column(Text, nullable=False)  # Base64 encoded QR code
    external_url = Column(String(500), nullable=False)  # URL that QR code points to
    title = Column(String(200))  # Custom title for QR code
    description = Column(Text)  # Description of QR code purpose
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # QR Code settings
    size = Column(Integer, default=200)  # QR code size in pixels
    error_correction = Column(String(10), default='M')  # L, M, Q, H
    border = Column(Integer, default=4)  # Border size
    background_color = Column(String(7), default='#FFFFFF')  # Hex color
    foreground_color = Column(String(7), default='#000000')  # Hex color
    
    # Analytics
    scan_count = Column(Integer, default=0)
    last_scanned = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    form = relationship("Form")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'form_id': self.form_id,
            'qr_code_data': self.qr_code_data,
            'external_url': self.external_url,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'size': self.size,
            'error_correction': self.error_correction,
            'border': self.border,
            'background_color': self.background_color,
            'foreground_color': self.foreground_color,
            'scan_count': self.scan_count,
            'last_scanned': self.last_scanned.isoformat() if self.last_scanned else None,
            'is_active': self.is_active
        }

class FormAccessCode(db.Model):
    """Real form access code model for controlled form access - NO MOCK DATA"""
    __tablename__ = 'form_access_codes'
    
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    access_code = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    max_uses = Column(Integer)  # Maximum number of uses
    current_uses = Column(Integer, default=0)
    
    # Relationships
    form = relationship("Form")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'form_id': self.form_id,
            'access_code': self.access_code,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses
        }

class QuickAccessToken(db.Model):
    """Real quick access token model for temporary authentication and form access - NO MOCK DATA"""
    __tablename__ = 'quick_access_tokens'
    
    id = Column(Integer, primary_key=True)
    token = Column(String(100), unique=True, nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(20))
    name = Column(String(100))
    access_type = Column(String(20), default='form_access')  # form_access, event_invite, etc.
    
    # OTP fields
    otp_code = Column(String(6))
    otp_expires_at = Column(DateTime)
    otp_verified = Column(Boolean, default=False)
    
    # Access control
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    max_uses = Column(Integer, default=5)  # Maximum number of form submissions
    current_uses = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Allowed forms (JSON array of form IDs)
    allowed_forms = Column(JSON)  # ["1", "2", "3"] or null for all public forms
    
    def is_valid(self):
        """Check if token is still valid"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True
    
    def can_access_form(self, form_id):
        """Check if token can access specific form"""
        if not self.is_valid():
            return False
        if not self.allowed_forms:  # null means access to all public forms
            return True
        return str(form_id) in self.allowed_forms
    
    def use_token(self):
        """Mark token as used - commit should be handled by service layer"""
        self.current_uses += 1
        self.last_used = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'token': self.token[:10] + '...' if self.token else None,
            'email': self.email,
            'phone': self.phone,
            'name': self.name,
            'access_type': self.access_type,
            'otp_verified': self.otp_verified,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'allowed_forms': self.allowed_forms
        }
