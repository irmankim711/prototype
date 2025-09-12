"""
Form-related Pydantic Schemas

This module contains all Pydantic models for form operations including:
- Form creation and updates
- Form field definitions
- Form submissions
- Form validation rules
- Form responses and listings
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum

from .common import BaseRequestSchema, BaseResponseSchema, SanitizedString, SanitizedHTML

# Form field types
class FieldType(str, Enum):
    """Supported form field types."""
    TEXT = "text"
    TEXTAREA = "textarea"
    EMAIL = "email"
    NUMBER = "number"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    FILE = "file"
    PASSWORD = "password"
    URL = "url"
    PHONE = "phone"
    ADDRESS = "address"
    SIGNATURE = "signature"
    RATING = "rating"
    SLIDER = "slider"
    COLOR = "color"
    HIDDEN = "hidden"

# Field validation types
class ValidationRule(str, Enum):
    """Supported validation rules."""
    REQUIRED = "required"
    MIN_LENGTH = "minLength"
    MAX_LENGTH = "maxLength"
    PATTERN = "pattern"
    MIN = "min"
    MAX = "max"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    DATE_RANGE = "dateRange"
    FILE_SIZE = "fileSize"
    FILE_TYPE = "fileType"
    CUSTOM = "custom"

class FormFieldSchema(BaseModel):
    """Schema for individual form fields."""
    id: str = Field(description="Unique field identifier")
    name: str = Field(description="Field name for form submission")
    label: SanitizedString = Field(description="Human-readable field label")
    type: FieldType = Field(description="Field type")
    placeholder: Optional[SanitizedString] = Field(default=None, description="Placeholder text")
    help_text: Optional[SanitizedString] = Field(default=None, description="Help text for the field")
    required: bool = Field(default=False, description="Whether the field is required")
    default_value: Optional[Any] = Field(default=None, description="Default field value")
    
    # Field-specific properties
    options: Optional[List[Dict[str, Any]]] = Field(default=None, description="Options for select/radio/checkbox fields")
    validation_rules: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    conditional_logic: Optional[Dict[str, Any]] = Field(default=None, description="Conditional display logic")
    
    # Styling and layout
    width: Optional[str] = Field(default=None, description="Field width (CSS value)")
    css_class: Optional[str] = Field(default=None, description="CSS classes")
    order: int = Field(default=0, description="Field display order")
    
    # Advanced features
    encrypted: bool = Field(default=False, description="Whether field data should be encrypted")
    sensitive: bool = Field(default=False, description="Whether field contains sensitive data")
    
    @validator('name')
    def validate_field_name(cls, v):
        """Validate field name format."""
        if not v or not v.strip():
            raise ValueError('Field name cannot be empty')
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Field name must start with letter or underscore and contain only alphanumeric characters and underscores')
        return v
    
    @validator('validation_rules')
    def validate_validation_rules(cls, v):
        """Validate validation rules structure."""
        if v is not None:
            for rule, value in v.items():
                if rule not in [rule.value for rule in ValidationRule]:
                    raise ValueError(f'Invalid validation rule: {rule}')
        return v

class FormValidationSchema(BaseModel):
    """Schema for form validation configuration."""
    required_fields: List[str] = Field(default_factory=list, description="List of required field names")
    custom_validators: Optional[Dict[str, Any]] = Field(default=None, description="Custom validation functions")
    cross_field_validation: Optional[List[Dict[str, Any]]] = Field(default=None, description="Cross-field validation rules")
    submission_limits: Optional[Dict[str, Any]] = Field(default=None, description="Submission rate limiting rules")

class FormCreateRequest(BaseRequestSchema):
    """Request schema for creating a new form."""
    title: SanitizedString = Field(..., min_length=1, max_length=200, description="Form title")
    description: Optional[SanitizedHTML] = Field(default=None, description="Form description")
    fields: List[FormFieldSchema] = Field(..., min_items=1, description="Form fields")
    
    # Form configuration
    is_public: bool = Field(default=False, description="Whether the form is publicly accessible")
    requires_authentication: bool = Field(default=False, description="Whether authentication is required")
    allow_anonymous: bool = Field(default=True, description="Whether anonymous submissions are allowed")
    max_submissions: Optional[int] = Field(default=None, ge=1, description="Maximum number of submissions")
    
    # Appearance and behavior
    theme: Optional[str] = Field(default="default", description="Form theme/style")
    redirect_url: Optional[str] = Field(default=None, description="URL to redirect after submission")
    success_message: Optional[SanitizedString] = Field(default=None, description="Success message after submission")
    
    # Advanced features
    enable_notifications: bool = Field(default=True, description="Enable email notifications")
    enable_analytics: bool = Field(default=True, description="Enable form analytics")
    enable_file_uploads: bool = Field(default=False, description="Enable file upload fields")
    
    # Security settings
    csrf_protection: bool = Field(default=True, description="Enable CSRF protection")
    rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    spam_protection: bool = Field(default=True, description="Enable spam protection")
    
    @validator('redirect_url')
    def validate_redirect_url(cls, v):
        """Validate redirect URL format."""
        if v is not None:
            if not v.startswith(('http://', 'https://', '/')):
                raise ValueError('Redirect URL must be absolute or relative')
        return v
    
    @validator('fields')
    def validate_fields(cls, v):
        """Validate form fields."""
        if not v:
            raise ValueError('Form must have at least one field')
        
        # Check for duplicate field names
        field_names = [field.name for field in v]
        if len(field_names) != len(set(field_names)):
            raise ValueError('Field names must be unique')
        
        # Validate file upload fields
        file_fields = [f for f in v if f.type == FieldType.FILE]
        if file_fields and not any(f.enable_file_uploads for f in v):
            raise ValueError('File upload fields require enable_file_uploads to be True')
        
        return v

class FormUpdateRequest(BaseRequestSchema):
    """Request schema for updating an existing form."""
    title: Optional[SanitizedString] = Field(default=None, min_length=1, max_length=200, description="Form title")
    description: Optional[SanitizedHTML] = Field(default=None, description="Form description")
    fields: Optional[List[FormFieldSchema]] = Field(default=None, min_items=1, description="Form fields")
    
    # Form configuration
    is_public: Optional[bool] = Field(default=None, description="Whether the form is publicly accessible")
    requires_authentication: Optional[bool] = Field(default=None, description="Whether authentication is required")
    allow_anonymous: Optional[bool] = Field(default=None, description="Whether anonymous submissions are allowed")
    max_submissions: Optional[int] = Field(default=None, ge=1, description="Maximum number of submissions")
    
    # Appearance and behavior
    theme: Optional[str] = Field(default=None, description="Form theme/style")
    redirect_url: Optional[str] = Field(default=None, description="URL to redirect after submission")
    success_message: Optional[SanitizedString] = Field(default=None, description="Success message after submission")
    
    # Advanced features
    enable_notifications: Optional[bool] = Field(default=None, description="Enable email notifications")
    enable_analytics: Optional[bool] = Field(default=None, description="Enable form analytics")
    enable_file_uploads: Optional[bool] = Field(default=None, description="Enable file upload fields")
    
    # Security settings
    csrf_protection: Optional[bool] = Field(default=None, description="Enable CSRF protection")
    rate_limiting: Optional[bool] = Field(default=None, description="Enable rate limiting")
    spam_protection: Optional[bool] = Field(default=None, description="Enable spam protection")
    
    @validator('redirect_url')
    def validate_redirect_url(cls, v):
        """Validate redirect URL format."""
        if v is not None:
            if not v.startswith(('http://', 'https://', '/')):
                raise ValueError('Redirect URL must be absolute or relative')
        return v

class FormSubmissionRequest(BaseRequestSchema):
    """Request schema for form submissions."""
    form_id: str = Field(..., description="ID of the form being submitted")
    data: Dict[str, Any] = Field(..., description="Form field data")
    
    # Optional metadata
    user_id: Optional[str] = Field(default=None, description="User ID if authenticated")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    ip_address: Optional[str] = Field(default=None, description="Submitter's IP address")
    user_agent: Optional[str] = Field(default=None, description="Submitter's user agent")
    
    # File uploads
    files: Optional[Dict[str, Any]] = Field(default=None, description="Uploaded files")
    
    # Additional context
    referrer: Optional[str] = Field(default=None, description="Referrer URL")
    utm_source: Optional[str] = Field(default=None, description="UTM source parameter")
    utm_medium: Optional[str] = Field(default=None, description="UTM medium parameter")
    utm_campaign: Optional[str] = Field(default=None, description="UTM campaign parameter")
    
    @validator('data')
    def validate_submission_data(cls, v):
        """Validate submission data structure."""
        if not isinstance(v, dict):
            raise ValueError('Submission data must be a dictionary')
        if not v:
            raise ValueError('Submission data cannot be empty')
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format."""
        if v is not None:
            import ipaddress
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v

class FormResponse(BaseResponseSchema):
    """Response schema for form data."""
    id: str = Field(description="Form unique identifier")
    title: str = Field(description="Form title")
    description: Optional[str] = Field(default=None, description="Form description")
    fields: List[FormFieldSchema] = Field(description="Form fields")
    
    # Form configuration
    is_public: bool = Field(description="Whether the form is publicly accessible")
    requires_authentication: bool = Field(description="Whether authentication is required")
    allow_anonymous: bool = Field(description="Whether anonymous submissions are allowed")
    max_submissions: Optional[int] = Field(default=None, description="Maximum number of submissions")
    
    # Appearance and behavior
    theme: str = Field(description="Form theme/style")
    redirect_url: Optional[str] = Field(default=None, description="URL to redirect after submission")
    success_message: Optional[str] = Field(default=None, description="Success message after submission")
    
    # Advanced features
    enable_notifications: bool = Field(description="Enable email notifications")
    enable_analytics: bool = Field(description="Enable form analytics")
    enable_file_uploads: bool = Field(description="Enable file upload fields")
    
    # Security settings
    csrf_protection: bool = Field(description="Enable CSRF protection")
    rate_limiting: bool = Field(description="Enable rate limiting")
    spam_protection: bool = Field(description="Enable spam protection")
    
    # Metadata
    created_at: datetime = Field(description="Form creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    created_by: Optional[str] = Field(default=None, description="User who created the form")
    status: str = Field(description="Form status")
    
    # Statistics
    submission_count: int = Field(default=0, description="Number of submissions")
    view_count: int = Field(default=0, description="Number of views")
    
    # Access control
    permissions: Optional[Dict[str, List[str]]] = Field(default=None, description="User permissions for this form")

class FormListResponse(BaseResponseSchema):
    """Response schema for form listings."""
    forms: List[FormResponse] = Field(description="List of forms")
    total: int = Field(description="Total number of forms")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    
    # Filtering and sorting
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Applied filters")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default=None, description="Sort order")

class FormSubmissionResponse(BaseResponseSchema):
    """Response schema for form submission results."""
    submission_id: str = Field(description="Submission unique identifier")
    form_id: str = Field(description="Form ID")
    status: str = Field(description="Submission status")
    message: str = Field(description="Submission result message")
    
    # Submission data
    data: Dict[str, Any] = Field(description="Submitted form data")
    submitted_at: datetime = Field(description="Submission timestamp")
    
    # User information
    user_id: Optional[str] = Field(default=None, description="User ID if authenticated")
    ip_address: Optional[str] = Field(default=None, description="Submitter's IP address")
    
    # Additional metadata
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    validation_errors: Optional[Dict[str, List[str]]] = Field(default=None, description="Validation errors if any")

class FormSearchRequest(BaseRequestSchema):
    """Request schema for searching forms."""
    query: Optional[str] = Field(default=None, description="Search query")
    status: Optional[str] = Field(default=None, description="Form status filter")
    created_by: Optional[str] = Field(default=None, description="Creator filter")
    is_public: Optional[bool] = Field(default=None, description="Public/private filter")
    has_file_uploads: Optional[bool] = Field(default=None, description="File upload capability filter")
    
    # Date range
    created_after: Optional[datetime] = Field(default=None, description="Created after date")
    created_before: Optional[datetime] = Field(default=None, description="Created before date")
    updated_after: Optional[datetime] = Field(default=None, description="Updated after date")
    updated_before: Optional[datetime] = Field(default=None, description="Updated before date")
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('created_after', 'created_before', 'updated_after', 'updated_before')
    def validate_date_ranges(cls, v, values):
        """Validate date range logic."""
        if v is not None:
            if 'created_after' in values and 'created_before' in values:
                if values['created_after'] and values['created_before']:
                    if values['created_after'] >= values['created_before']:
                        raise ValueError('created_after must be before created_before')
            if 'updated_after' in values and 'updated_before' in values:
                if values['updated_after'] and values['updated_before']:
                    if values['updated_after'] >= values['updated_before']:
                        raise ValueError('updated_after must be before updated_before')
        return v

# Import regex for validation
import re
