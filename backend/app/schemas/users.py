"""
User-related Pydantic Schemas

This module contains all Pydantic models for user operations including:
- User creation and updates
- Authentication requests
- User responses and listings
- Permission and role management
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, root_validator, EmailStr
from datetime import datetime
from enum import Enum

from .common import BaseRequestSchema, BaseResponseSchema, SanitizedString

# User role types
class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"

# User status types
class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"

# Permission types
class Permission(str, Enum):
    """Permission enumeration."""
    # Report permissions
    CREATE_REPORT = "create_report"
    READ_REPORT = "read_report"
    UPDATE_REPORT = "update_report"
    DELETE_REPORT = "delete_report"
    EXPORT_REPORT = "export_report"
    
    # User management permissions
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Template permissions
    CREATE_TEMPLATE = "create_template"
    UPDATE_TEMPLATE = "update_template"
    DELETE_TEMPLATE = "delete_template"
    VIEW_TEMPLATE = "view_template"
    
    # Dashboard permissions
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_DASHBOARD = "manage_dashboard"
    
    # File permissions
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    DELETE_FILE = "delete_file"
    VIEW_FILE = "view_file"
    
    # Form permissions
    CREATE_FORM = "create_form"
    UPDATE_FORM = "update_form"
    DELETE_FORM = "delete_form"
    VIEW_FORM = "view_form"
    SUBMIT_FORM = "submit_form"
    
    # System permissions
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    MANAGE_SETTINGS = "manage_settings"

class UserCreateRequest(BaseRequestSchema):
    """Request schema for creating a new user."""
    email: EmailStr = Field(..., description="User email address")
    username: SanitizedString = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    # Personal information
    first_name: SanitizedString = Field(..., min_length=1, max_length=50, description="First name")
    last_name: SanitizedString = Field(..., min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    company: Optional[SanitizedString] = Field(default=None, max_length=100, description="Company name")
    job_title: Optional[SanitizedString] = Field(default=None, max_length=100, description="Job title")
    bio: Optional[SanitizedString] = Field(default=None, max_length=500, description="User biography")
    
    # Account settings
    role: UserRole = Field(default=UserRole.USER, description="User role")
    timezone: str = Field(default="UTC", description="User timezone")
    language: str = Field(default="en", description="Preferred language")
    theme: str = Field(default="light", regex="^(light|dark|auto)$", description="UI theme preference")
    
    # Preferences
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    push_notifications: bool = Field(default=False, description="Enable push notifications")
    
    # Security
    require_password_change: bool = Field(default=False, description="Require password change on first login")
    two_factor_enabled: bool = Field(default=False, description="Enable two-factor authentication")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is not None:
            import re
            # Basic phone validation - adjust regex as needed
            if not re.match(r'^[\+]?[1-9][\d]{0,15}$', v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')):
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('confirm_password')
    def validate_password_confirmation(cls, v, values):
        """Validate password confirmation matches."""
        if 'password' in values and v != values['password']:
            raise ValueError('Password confirmation does not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for common patterns
        if v.lower() in ['password', '123456', 'qwerty', 'admin']:
            raise ValueError('Password is too common')
        
        # Check for complexity (at least one uppercase, lowercase, digit)
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v

class UserUpdateRequest(BaseRequestSchema):
    """Request schema for updating an existing user."""
    email: Optional[EmailStr] = Field(default=None, description="User email address")
    username: Optional[SanitizedString] = Field(default=None, min_length=3, max_length=50, description="Username")
    
    # Personal information
    first_name: Optional[SanitizedString] = Field(default=None, min_length=1, max_length=50, description="First name")
    last_name: Optional[SanitizedString] = Field(default=None, min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    company: Optional[SanitizedString] = Field(default=None, max_length=100, description="Company name")
    job_title: Optional[SanitizedString] = Field(default=None, max_length=100, description="Job title")
    bio: Optional[SanitizedString] = Field(default=None, max_length=500, description="User biography")
    
    # Account settings
    role: Optional[UserRole] = Field(default=None, description="User role")
    timezone: Optional[str] = Field(default=None, description="User timezone")
    language: Optional[str] = Field(default=None, description="Preferred language")
    theme: Optional[str] = Field(default=None, regex="^(light|dark|auto)$", description="UI theme preference")
    
    # Preferences
    email_notifications: Optional[bool] = Field(default=None, description="Enable email notifications")
    push_notifications: Optional[bool] = Field(default=None, description="Enable push notifications")
    
    # Security
    require_password_change: Optional[bool] = Field(default=None, description="Require password change on next login")
    two_factor_enabled: Optional[bool] = Field(default=None, description="Enable two-factor authentication")
    
    # Status
    status: Optional[UserStatus] = Field(default=None, description="User status")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is not None:
            import re
            if not re.match(r'^[\+]?[1-9][\d]{0,15}$', v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')):
                raise ValueError('Invalid phone number format')
        return v

class UserLoginRequest(BaseRequestSchema):
    """Request schema for user authentication."""
    identifier: str = Field(..., description="Email or username")
    password: str = Field(..., description="User password")
    
    # Additional authentication options
    remember_me: bool = Field(default=False, description="Remember user session")
    two_factor_code: Optional[str] = Field(default=None, description="Two-factor authentication code")
    
    # Security context
    device_info: Optional[Dict[str, Any]] = Field(default=None, description="Device information")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Geographic location")
    
    @validator('identifier')
    def validate_identifier(cls, v):
        """Validate identifier format."""
        if not v or not v.strip():
            raise ValueError('Identifier cannot be empty')
        return v.strip()

class UserPasswordChangeRequest(BaseRequestSchema):
    """Request schema for changing user password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('confirm_new_password')
    def validate_password_confirmation(cls, v, values):
        """Validate password confirmation matches."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Password confirmation does not match')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for common patterns
        if v.lower() in ['password', '123456', 'qwerty', 'admin']:
            raise ValueError('Password is too common')
        
        # Check for complexity
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain at least one uppercase letter, one lowercase letter, and one digit')
        
        return v

class UserResponse(BaseResponseSchema):
    """Response schema for user data."""
    id: str = Field(description="User unique identifier")
    email: str = Field(description="User email address")
    username: str = Field(description="Username")
    
    # Personal information
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    company: Optional[str] = Field(default=None, description="Company name")
    job_title: Optional[str] = Field(default=None, description="Job title")
    bio: Optional[str] = Field(default=None, description="User biography")
    avatar_url: Optional[str] = Field(default=None, description="Avatar image URL")
    
    # Account settings
    role: UserRole = Field(description="User role")
    status: UserStatus = Field(description="User status")
    timezone: str = Field(description="User timezone")
    language: str = Field(description="Preferred language")
    theme: str = Field(description="UI theme preference")
    
    # Preferences
    email_notifications: bool = Field(description="Enable email notifications")
    push_notifications: bool = Field(description="Enable push notifications")
    
    # Security
    two_factor_enabled: bool = Field(description="Two-factor authentication enabled")
    last_password_change: Optional[datetime] = Field(default=None, description="Last password change timestamp")
    require_password_change: bool = Field(description="Password change required")
    
    # Metadata
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    
    # Statistics
    login_count: int = Field(default=0, description="Number of successful logins")
    failed_login_attempts: int = Field(default=0, description="Number of failed login attempts")
    
    # Permissions
    permissions: List[Permission] = Field(description="User permissions")
    role_permissions: Dict[str, List[Permission]] = Field(description="Permissions by role")

class UserListResponse(BaseResponseSchema):
    """Response schema for user listings."""
    users: List[UserResponse] = Field(description="List of users")
    total: int = Field(description="Total number of users")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    
    # Filtering and sorting
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Applied filters")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default=None, description="Sort order")
    
    # Summary statistics
    status_counts: Dict[str, int] = Field(description="Count of users by status")
    role_counts: Dict[str, int] = Field(description="Count of users by role")

class UserSearchRequest(BaseRequestSchema):
    """Request schema for searching users."""
    query: Optional[str] = Field(default=None, description="Search query")
    role: Optional[UserRole] = Field(default=None, description="Role filter")
    status: Optional[UserStatus] = Field(default=None, description="Status filter")
    company: Optional[str] = Field(default=None, description="Company filter")
    
    # Date range
    created_after: Optional[datetime] = Field(default=None, description="Created after date")
    created_before: Optional[datetime] = Field(default=None, description="Created before date")
    last_login_after: Optional[datetime] = Field(default=None, description="Last login after date")
    last_login_before: Optional[datetime] = Field(default=None, description="Last login before date")
    
    # Access control
    has_permission: Optional[Permission] = Field(default=None, description="Permission filter")
    is_active: Optional[bool] = Field(default=None, description="Active status filter")
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('created_after', 'created_before', 'last_login_after', 'last_login_before')
    def validate_date_ranges(cls, v, values):
        """Validate date range logic."""
        if v is not None:
            if 'created_after' in values and 'created_before' in values:
                if values['created_after'] and values['created_before']:
                    if values['created_after'] >= values['created_before']:
                        raise ValueError('created_after must be before created_before')
            if 'last_login_after' in values and 'last_login_before' in values:
                if values['last_login_after'] and values['last_login_before']:
                    if values['last_login_after'] >= values['last_login_before']:
                        raise ValueError('last_login_after must be before last_login_before')
        return v

class PermissionResponse(BaseResponseSchema):
    """Response schema for permission information."""
    permission: Permission = Field(description="Permission identifier")
    name: str = Field(description="Human-readable permission name")
    description: str = Field(description="Permission description")
    category: str = Field(description="Permission category")
    is_dangerous: bool = Field(description="Whether permission is dangerous")

class RoleResponse(BaseResponseSchema):
    """Response schema for role information."""
    role: UserRole = Field(description="Role identifier")
    name: str = Field(description="Human-readable role name")
    description: str = Field(description="Role description")
    permissions: List[Permission] = Field(description="Role permissions")
    is_system: bool = Field(description="Whether role is system-defined")
    can_be_assigned: bool = Field(description="Whether role can be assigned to users")
