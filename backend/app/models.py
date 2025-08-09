from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
from typing import Optional

# Role and Permission Models for RBAC
class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class Permission(Enum):
    # Report permissions
    CREATE_REPORT = "create_report"
    READ_REPORT = "read_report"
    UPDATE_REPORT = "update_report"
    DELETE_REPORT = "delete_report"
    
    # User management permissions
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # Template permissions
    CREATE_TEMPLATE = "create_template"
    UPDATE_TEMPLATE = "update_template"
    DELETE_TEMPLATE = "delete_template"
    
    # Dashboard permissions
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_ANALYTICS = "view_analytics"
    
    # File permissions
    UPLOAD_FILE = "upload_file"
    DELETE_FILE = "delete_file"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(Permission),  # Admin has all permissions
    UserRole.MANAGER: [
        Permission.CREATE_REPORT, Permission.READ_REPORT, Permission.UPDATE_REPORT, Permission.DELETE_REPORT,
        Permission.VIEW_USERS, Permission.CREATE_TEMPLATE, Permission.UPDATE_TEMPLATE,
        Permission.VIEW_DASHBOARD, Permission.VIEW_ANALYTICS, Permission.UPLOAD_FILE, Permission.DELETE_FILE
    ],
    UserRole.USER: [
        Permission.CREATE_REPORT, Permission.READ_REPORT, Permission.UPDATE_REPORT,
        Permission.VIEW_DASHBOARD, Permission.UPLOAD_FILE
    ],
    UserRole.VIEWER: [
        Permission.READ_REPORT, Permission.VIEW_DASHBOARD
    ]
}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Increased size for scrypt hashes
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    theme = db.Column(db.String(20), default='light')
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    is_active = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    reports = db.relationship('Report', backref='author', lazy=True)
    forms = db.relationship('Form', backref='creator', lazy=True)

    def set_password(self, password: str):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True if password matches stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission based on their role."""
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def get_permissions(self) -> list:
        """Get all permissions for user's role."""
        return ROLE_PERMISSIONS.get(self.role, [])
    
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template_id = db.Column(db.String(120))
    data = db.Column(db.JSON)
    output_url = db.Column(db.String(500))
    
    # ✅ FIXED: Explicit constructor for proper type checking
    def __init__(self, title: str, user_id: int, description: Optional[str] = None, 
                 template_id: Optional[str] = None, data: Optional[dict] = None, 
                 status: str = 'draft', output_url: Optional[str] = None, **kwargs):
        """Report model constructor with proper type hints"""
        super(Report, self).__init__(**kwargs)
        self.title = title
        self.user_id = user_id
        self.description = description
        self.template_id = template_id
        self.data = data or {}
        self.status = status
        self.output_url = output_url

class ReportTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    schema = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Form Builder Models
class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    schema = db.Column(db.JSON)  # Form structure definition
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New fields for enhanced form builder
    external_url = db.Column(db.String(500))  # External URL for form sharing
    qr_code_data = db.Column(db.Text)  # Base64 encoded QR code
    form_settings = db.Column(db.JSON)  # Additional form settings (themes, notifications, etc.)
    access_key = db.Column(db.String(100))  # Unique access key for public forms
    view_count = db.Column(db.Integer, default=0)  # Track form views
    submission_limit = db.Column(db.Integer)  # Optional submission limit
    expires_at = db.Column(db.DateTime)  # Optional expiration date
    
    # Relationships
    submissions = db.relationship('FormSubmission', backref='form', lazy=True, cascade='all, delete-orphan')
    qr_codes = db.relationship('FormQRCode', backref='form', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(Form, self).__init__(**kwargs)

class FormSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    data = db.Column(db.JSON)  # Submitted form data
    submitter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitter_email = db.Column(db.String(120))  # For anonymous submissions
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='submitted')  # submitted, reviewed, approved, rejected
    
    # Enhanced submission tracking
    ip_address = db.Column(db.String(45))  # IPv4/IPv6 support
    user_agent = db.Column(db.Text)
    submission_source = db.Column(db.String(50), default='web')  # web, qr_code, api, mobile
    location_data = db.Column(db.JSON)  # Optional location information
    processing_notes = db.Column(db.Text)  # Admin notes for processing

    # ✅ FIXED: Explicit constructor for FormSubmission 
    def __init__(self, form_id: int, data: Optional[dict] = None, 
                 submitter_id: Optional[int] = None, submitter_email: Optional[str] = None,
                 ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                 submission_source: str = 'web', status: str = 'submitted', **kwargs):
        """FormSubmission model constructor with proper type hints"""
        super(FormSubmission, self).__init__(**kwargs)
        self.form_id = form_id
        self.data = data or {}
        self.submitter_id = submitter_id
        self.submitter_email = submitter_email
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.submission_source = submission_source
        self.status = status

# New model for QR Code management
class FormQRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    qr_code_data = db.Column(db.Text, nullable=False)  # Base64 encoded QR code
    external_url = db.Column(db.String(500), nullable=False)  # URL that QR code points to
    title = db.Column(db.String(200))  # Custom title for QR code
    description = db.Column(db.Text)  # Description of QR code purpose
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # QR Code settings
    size = db.Column(db.Integer, default=200)  # QR code size in pixels
    error_correction = db.Column(db.String(10), default='M')  # L, M, Q, H
    border = db.Column(db.Integer, default=4)  # Border size
    background_color = db.Column(db.String(7), default='#FFFFFF')  # Hex color
    foreground_color = db.Column(db.String(7), default='#000000')  # Hex color

    def __init__(self, **kwargs):
        super(FormQRCode, self).__init__(**kwargs)
    
    # Analytics
    scan_count = db.Column(db.Integer, default=0)
    last_scanned = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

# File Management Models
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_files')

# Quick Access Authentication Model
class QuickAccessToken(db.Model):
    __tablename__ = 'quick_access_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    name = db.Column(db.String(100))
    access_type = db.Column(db.String(20), default='form_access')  # form_access, event_invite, etc.
    
    # OTP fields
    otp_code = db.Column(db.String(6))
    otp_expires_at = db.Column(db.DateTime)
    otp_verified = db.Column(db.Boolean, default=False)
    
    # Access control
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer, default=5)  # Maximum number of form submissions
    current_uses = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    # Allowed forms (JSON array of form IDs)
    allowed_forms = db.Column(db.JSON)  # ["1", "2", "3"] or null for all public forms
    
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
        """Mark token as used"""
        self.current_uses += 1
        self.last_used = datetime.utcnow()
        db.session.commit()

# Form Access Code Model for Public Form Access (Generic - Multiple Forms)
class FormAccessCode(db.Model):
    __tablename__ = 'form_access_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)  # Name for this access code
    description = db.Column(db.Text)  # Description of what this code provides access to
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer)
    current_uses = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # JSON array of form IDs that this code can access
    allowed_form_ids = db.Column(db.JSON)  # [1, 2, 3, ...] - list of form IDs
    
    # JSON array of external form objects
    allowed_external_forms = db.Column(db.JSON)  # [{"title": "...", "url": "...", "description": "..."}, ...]
    
    # Relationships
    creator = db.relationship('User', backref='created_access_codes')
    
    def is_valid(self):
        """Check if access code is still valid"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True
    
    def use_code(self):
        """Mark code as used"""
        if self.max_uses:
            self.current_uses += 1
            db.session.commit()
    
    def can_access_form(self, form_id):
        """Check if this code can access a specific form"""
        if not self.is_valid():
            return False
        if not self.allowed_form_ids:
            return False
        return form_id in self.allowed_form_ids
    
    def get_accessible_forms(self):
        """Get all forms this code can access"""
        accessible_forms = []
        
        # Get internal forms
        if self.allowed_form_ids:
            forms = Form.query.filter(
                Form.id.in_(self.allowed_form_ids),
                Form.is_active == True
            ).all()
            
            for form in forms:
                accessible_forms.append({
                    'id': form.id,
                    'title': form.title,
                    'description': form.description,
                    'type': 'internal',
                    'is_public': form.is_public,
                    'created_at': form.created_at.isoformat() if form.created_at else None,
                    'field_count': len(form.schema) if form.schema else 0
                })
        
        # Get external forms
        if self.allowed_external_forms:
            for ext_form in self.allowed_external_forms:
                accessible_forms.append({
                    'id': f"external_{ext_form.get('id', 'unknown')}",
                    'title': ext_form.get('title', 'External Form'),
                    'description': ext_form.get('description', ''),
                    'type': 'external',
                    'external_url': ext_form.get('url', ''),
                    'created_at': ext_form.get('created_at', ''),
                    'field_count': 0
                })
        
        return accessible_forms
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'created_by': self.created_by,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'allowed_form_ids': self.allowed_form_ids or [],
            'allowed_external_forms': self.allowed_external_forms or [],
            'accessible_forms_count': len(self.get_accessible_forms())
        }
