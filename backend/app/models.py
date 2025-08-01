from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

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
