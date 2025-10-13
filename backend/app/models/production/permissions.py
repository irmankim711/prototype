"""
Permission and Role Models for production deployment
NO MOCK DATA - Real permission management
"""

from enum import Enum

class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_USER = "api_user"

class Permission(Enum):
    """Permission enumeration"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    MANAGE_FORMS = "manage_forms"
    MANAGE_REPORTS = "manage_reports"
    EXPORT_DATA = "export_data"
    UPLOAD_FILE = "upload_file"
