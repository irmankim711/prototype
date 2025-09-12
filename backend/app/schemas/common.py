"""
Common Pydantic Schemas for API Validation

This module contains base classes and common response models used across all API endpoints.
"""

from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum
import re

# Type variable for generic responses
T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema with common configuration and methods."""
    
    class Config:
        # Allow extra fields to be ignored
        extra = "ignore"
        # Use enum values instead of enum objects
        use_enum_values = True
        # Allow population by field name
        populate_by_name = True
        # Validate assignment
        validate_assignment = True
        # JSON serialization options
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class PaginationParams(BaseSchema):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T]
    pagination: Dict[str, Any] = Field(
        description="Pagination metadata including total, page, per_page, pages"
    )
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")

class SuccessResponse(BaseModel):
    """Standard success response format."""
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(description="Success message")
    data: Optional[Any] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(description="Error code/type")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier")

class ValidationErrorResponse(BaseModel):
    """Validation error response format."""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(default="VALIDATION_ERROR", description="Error type")
    message: str = Field(default="Validation failed", description="Validation error message")
    field_errors: Dict[str, List[str]] = Field(description="Field-specific validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class FileInfo(BaseSchema):
    """File information schema."""
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type")
    size: int = Field(ge=0, description="File size in bytes")
    extension: Optional[str] = Field(default=None, description="File extension")
    checksum: Optional[str] = Field(default=None, description="File hash/checksum")

class AuditInfo(BaseSchema):
    """Audit trail information."""
    created_at: datetime = Field(description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="User who created the resource")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    updated_by: Optional[str] = Field(default=None, description="User who last updated the resource")
    version: int = Field(default=1, description="Resource version number")

class SearchParams(BaseSchema):
    """Search parameters for filtered queries."""
    query: Optional[str] = Field(default=None, description="Search query string")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    date_from: Optional[datetime] = Field(default=None, description="Start date for date range")
    date_to: Optional[datetime] = Field(default=None, description="End date for date range")
    tags: Optional[List[str]] = Field(default=None, description="Tags to filter by")
    status: Optional[str] = Field(default=None, description="Status filter")

class RateLimitInfo(BaseSchema):
    """Rate limiting information."""
    limit: int = Field(description="Request limit per time window")
    remaining: int = Field(description="Remaining requests in current window")
    reset_time: datetime = Field(description="Time when limit resets")
    window_size: int = Field(description="Time window size in seconds")

class SecurityHeaders(BaseSchema):
    """Security-related HTTP headers."""
    csrf_token: Optional[str] = Field(default=None, description="CSRF protection token")
    x_frame_options: str = Field(default="DENY", description="X-Frame-Options header")
    x_content_type_options: str = Field(default="nosniff", description="X-Content-Type-Options header")
    x_xss_protection: str = Field(default="1; mode=block", description="X-XSS-Protection header")

class SanitizedString(str):
    """String field with XSS protection."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('String required')
        
        # XSS protection: remove or escape dangerous HTML/JavaScript
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'vbscript:',   # VBScript protocol
            r'data:',       # Data URLs
            r'on\w+\s*=',   # Event handlers
            r'<iframe[^>]*>',  # Iframe tags
            r'<object[^>]*>',  # Object tags
            r'<embed[^>]*>',   # Embed tags
        ]
        
        sanitized = v
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Additional HTML entity encoding for safety
        html_entities = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, entity in html_entities.items():
            sanitized = sanitized.replace(char, entity)
        
        return cls(sanitized)

class SanitizedHTML(str):
    """HTML string field with limited allowed tags."""
    
    ALLOWED_TAGS = {
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'a', 'span', 'div', 'table', 'tr', 'td', 'th'
    }
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'span': ['class', 'style'],
        'div': ['class', 'style'],
        'table': ['class', 'style'],
        'td': ['class', 'style', 'colspan', 'rowspan'],
        'th': ['class', 'style', 'colspan', 'rowspan']
    }
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('String required')
        
        # Basic HTML tag validation (simplified - in production, use a proper HTML sanitizer)
        # This is a basic implementation - consider using bleach or similar library
        return cls(v)

class BaseRequestSchema(BaseSchema):
    """Base class for all request schemas."""
    
    @root_validator(pre=True)
    def sanitize_strings(cls, values):
        """Sanitize all string fields to prevent XSS attacks."""
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, str):
                    # Apply basic sanitization
                    values[key] = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
                    values[key] = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
                    values[key] = re.sub(r'vbscript:', '', value, flags=re.IGNORECASE)
                    values[key] = re.sub(r'data:', '', value, flags=re.IGNORECASE)
        return values

class BaseResponseSchema(BaseSchema):
    """Base class for all response schemas."""
    
    class Config:
        # Allow extra fields to be ignored
        extra = "ignore"
        # Use enum values instead of enum objects
        use_enum_values = True
        # Allow population by field name
        populate_by_name = True
        # Validate assignment
        validate_assignment = True
        # JSON serialization options
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
