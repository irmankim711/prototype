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
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    is_active = db.Column(db.Boolean, default=True)
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
    
    # Relationships
    submissions = db.relationship('FormSubmission', backref='form', lazy=True, cascade='all, delete-orphan')

class FormSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    data = db.Column(db.JSON)  # Submitted form data
    submitter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitter_email = db.Column(db.String(120))  # For anonymous submissions
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='submitted')  # submitted, reviewed, approved, rejected

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
