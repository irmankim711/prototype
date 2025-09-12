"""
File-related Pydantic Schemas

This module contains all Pydantic models for file operations including:
- File uploads and validation
- File metadata and information
- File access control
- File processing and conversion
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum
import mimetypes
import os

from .common import BaseRequestSchema, BaseResponseSchema, SanitizedString

# File types
class FileType(str, Enum):
    """File type enumeration."""
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    CODE = "code"
    DATA = "data"
    OTHER = "other"

# File status
class FileStatus(str, Enum):
    """File status enumeration."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"
    ARCHIVED = "archived"

# Allowed file extensions by type
ALLOWED_EXTENSIONS = {
    FileType.DOCUMENT: ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    FileType.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],
    FileType.VIDEO: ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'],
    FileType.AUDIO: ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
    FileType.ARCHIVE: ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    FileType.SPREADSHEET: ['.xls', '.xlsx', '.csv', '.ods'],
    FileType.PRESENTATION: ['.ppt', '.pptx', '.odp'],
    FileType.CODE: ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php'],
    FileType.DATA: ['.json', '.xml', '.yaml', '.yml', '.sql', '.db']
}

# Allowed MIME types by file type
ALLOWED_MIME_TYPES = {
    FileType.DOCUMENT: [
        'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain', 'application/rtf', 'application/vnd.oasis.opendocument.text'
    ],
    FileType.IMAGE: [
        'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/svg+xml', 'image/webp', 'image/tiff'
    ],
    FileType.VIDEO: [
        'video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-ms-wmv', 'video/x-flv', 'video/webm', 'video/x-matroska'
    ],
    FileType.AUDIO: [
        'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg', 'audio/x-ms-wma'
    ],
    FileType.ARCHIVE: [
        'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
        'application/x-tar', 'application/gzip', 'application/x-bzip2'
    ],
    FileType.SPREADSHEET: [
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv', 'application/vnd.oasis.opendocument.spreadsheet'
    ],
    FileType.PRESENTATION: [
        'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.oasis.opendocument.presentation'
    ],
    FileType.CODE: [
        'text/x-python', 'application/javascript', 'text/html', 'text/css', 'text/x-java-source',
        'text/x-c++src', 'text/x-csrc', 'application/x-httpd-php'
    ],
    FileType.DATA: [
        'application/json', 'application/xml', 'text/yaml', 'application/sql', 'application/x-sqlite3'
    ]
}

class FileValidationSchema(BaseModel):
    """Schema for file validation rules."""
    max_file_size: int = Field(default=10 * 1024 * 1024, ge=1, description="Maximum file size in bytes")
    allowed_extensions: List[str] = Field(default_factory=list, description="Allowed file extensions")
    allowed_mime_types: List[str] = Field(default_factory=list, description="Allowed MIME types")
    scan_for_viruses: bool = Field(default=True, description="Scan files for viruses")
    validate_content: bool = Field(default=True, description="Validate file content integrity")
    require_metadata: bool = Field(default=False, description="Require file metadata")
    
    # Content validation
    max_dimensions: Optional[Dict[str, int]] = Field(default=None, description="Maximum dimensions for images/videos")
    min_dimensions: Optional[Dict[str, int]] = Field(default=None, description="Minimum dimensions for images/videos")
    allowed_resolutions: Optional[List[str]] = Field(default=None, description="Allowed resolutions")
    
    # Security
    block_executables: bool = Field(default=True, description="Block executable files")
    block_scripts: bool = Field(default=False, description="Block script files")
    require_authentication: bool = Field(default=True, description="Require authentication for uploads")
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        """Validate maximum file size is reasonable."""
        max_allowed = 100 * 1024 * 1024  # 100MB
        if v > max_allowed:
            raise ValueError(f'Maximum file size cannot exceed {max_allowed // (1024 * 1024)}MB')
        return v
    
    @validator('allowed_extensions')
    def validate_extensions(cls, v):
        """Validate file extensions format."""
        for ext in v:
            if not ext.startswith('.'):
                raise ValueError(f'File extension must start with dot: {ext}')
            if not ext[1:].isalnum():
                raise ValueError(f'File extension contains invalid characters: {ext}')
        return v

class FileUploadRequest(BaseRequestSchema):
    """Request schema for file uploads."""
    filename: SanitizedString = Field(..., description="Original filename")
    content_type: str = Field(..., description="File MIME type")
    file_size: int = Field(..., ge=1, description="File size in bytes")
    
    # File metadata
    description: Optional[SanitizedString] = Field(default=None, max_length=500, description="File description")
    tags: List[str] = Field(default_factory=list, description="File tags")
    category: Optional[str] = Field(default=None, description="File category")
    
    # Access control
    is_public: bool = Field(default=False, description="Whether file is publicly accessible")
    allowed_users: Optional[List[str]] = Field(default=None, description="List of allowed user IDs")
    allowed_roles: Optional[List[str]] = Field(default=None, description="List of allowed roles")
    
    # Processing options
    generate_thumbnail: bool = Field(default=True, description="Generate thumbnail for images/videos")
    extract_metadata: bool = Field(default=True, description="Extract file metadata")
    create_preview: bool = Field(default=False, description="Create preview version")
    
    # Security
    encrypt_file: bool = Field(default=False, description="Encrypt file content")
    scan_for_viruses: bool = Field(default=True, description="Scan file for viruses")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename format."""
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f'Filename contains invalid character: {char}')
        
        # Check length
        if len(v) > 255:
            raise ValueError('Filename too long (max 255 characters)')
        
        return v.strip()
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate MIME type format."""
        if not v or '/' not in v:
            raise ValueError('Invalid MIME type format')
        
        # Check if it's a valid MIME type
        if not mimetypes.guess_extension(v):
            raise ValueError('Invalid or unsupported MIME type')
        
        return v
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size."""
        max_size = 100 * 1024 * 1024  # 100MB
        if v > max_size:
            raise ValueError(f'File size exceeds maximum allowed size of {max_size // (1024 * 1024)}MB')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate file tags."""
        if len(v) > 20:
            raise ValueError('Too many tags (max 20)')
        
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError('Tag cannot be empty')
            if len(tag) > 50:
                raise ValueError(f'Tag too long: {tag}')
            if not tag.replace('-', '').replace('_', '').isalnum():
                raise ValueError(f'Tag contains invalid characters: {tag}')
        
        return [tag.strip() for tag in v]

class FileResponse(BaseResponseSchema):
    """Response schema for file data."""
    id: str = Field(description="File unique identifier")
    filename: str = Field(description="Original filename")
    display_name: str = Field(description="Display name for the file")
    
    # File information
    content_type: str = Field(description="File MIME type")
    file_size: int = Field(description="File size in bytes")
    file_type: FileType = Field(description="File type category")
    extension: str = Field(description="File extension")
    
    # File status and processing
    status: FileStatus = Field(description="File processing status")
    checksum: str = Field(description="File checksum/hash")
    virus_scan_status: Optional[str] = Field(default=None, description="Virus scan status")
    
    # Metadata
    description: Optional[str] = Field(default=None, description="File description")
    tags: List[str] = Field(description="File tags")
    category: Optional[str] = Field(default=None, description="File category")
    
    # Access control
    is_public: bool = Field(description="Whether file is publicly accessible")
    allowed_users: Optional[List[str]] = Field(default=None, description="List of allowed user IDs")
    allowed_roles: Optional[List[str]] = Field(default=None, description="List of allowed roles")
    
    # File locations
    file_path: str = Field(description="File storage path")
    download_url: Optional[str] = Field(default=None, description="Download URL")
    preview_url: Optional[str] = Field(default=None, description="Preview URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")
    
    # Processing results
    thumbnail_generated: bool = Field(description="Whether thumbnail was generated")
    metadata_extracted: bool = Field(description="Whether metadata was extracted")
    preview_created: bool = Field(description="Whether preview was created")
    
    # File-specific metadata
    dimensions: Optional[Dict[str, int]] = Field(default=None, description="Image/video dimensions")
    duration: Optional[float] = Field(default=None, description="Audio/video duration")
    resolution: Optional[str] = Field(default=None, description="Image/video resolution")
    bitrate: Optional[int] = Field(default=None, description="Audio/video bitrate")
    
    # Timestamps
    uploaded_at: datetime = Field(description="Upload timestamp")
    processed_at: Optional[datetime] = Field(default=None, description="Processing completion timestamp")
    last_accessed: Optional[datetime] = Field(default=None, description="Last access timestamp")
    
    # User information
    uploaded_by: str = Field(description="User who uploaded the file")
    
    # Statistics
    download_count: int = Field(default=0, description="Number of downloads")
    view_count: int = Field(default=0, description="Number of views")
    
    # Security
    is_encrypted: bool = Field(description="Whether file is encrypted")
    encryption_key_id: Optional[str] = Field(default=None, description="Encryption key identifier")

class FileListResponse(BaseResponseSchema):
    """Response schema for file listings."""
    files: List[FileResponse] = Field(description="List of files")
    total: int = Field(description="Total number of files")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    
    # Filtering and sorting
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Applied filters")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default=None, description="Sort order")
    
    # Summary statistics
    total_size: int = Field(description="Total size of all files")
    type_counts: Dict[str, int] = Field(description="Count of files by type")
    status_counts: Dict[str, int] = Field(description="Count of files by status")

class FileSearchRequest(BaseRequestSchema):
    """Request schema for searching files."""
    query: Optional[str] = Field(default=None, description="Search query")
    file_type: Optional[FileType] = Field(default=None, description="File type filter")
    status: Optional[FileStatus] = Field(default=None, description="Status filter")
    uploaded_by: Optional[str] = Field(default=None, description="Uploader filter")
    category: Optional[str] = Field(default=None, description="Category filter")
    tags: Optional[List[str]] = Field(default=None, description="Tag filter")
    
    # File size range
    min_size: Optional[int] = Field(default=None, ge=0, description="Minimum file size")
    max_size: Optional[int] = Field(default=None, ge=1, description="Maximum file size")
    
    # Date range
    uploaded_after: Optional[datetime] = Field(default=None, description="Uploaded after date")
    uploaded_before: Optional[datetime] = Field(default=None, description="Uploaded before date")
    modified_after: Optional[datetime] = Field(default=None, description="Modified after date")
    modified_before: Optional[datetime] = Field(default=None, description="Modified before date")
    
    # Access control
    is_public: Optional[bool] = Field(default=None, description="Public/private filter")
    user_accessible: Optional[bool] = Field(default=None, description="User accessibility filter")
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field(default="uploaded_at", description="Sort field")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('min_size', 'max_size')
    def validate_size_range(cls, v, values):
        """Validate file size range logic."""
        if v is not None:
            if 'min_size' in values and 'max_size' in values:
                if values['min_size'] and values['max_size']:
                    if values['min_size'] >= values['max_size']:
                        raise ValueError('min_size must be less than max_size')
        return v
    
    @validator('uploaded_after', 'uploaded_before', 'modified_after', 'modified_before')
    def validate_date_ranges(cls, v, values):
        """Validate date range logic."""
        if v is not None:
            if 'uploaded_after' in values and 'uploaded_before' in values:
                if values['uploaded_after'] and values['uploaded_before']:
                    if values['uploaded_after'] >= values['uploaded_before']:
                        raise ValueError('uploaded_after must be before uploaded_before')
            if 'modified_after' in values and 'modified_before' in values:
                if values['modified_after'] and values['modified_before']:
                    if values['modified_after'] >= values['modified_before']:
                        raise ValueError('modified_after must be before modified_before')
        return v

class FileProcessingRequest(BaseRequestSchema):
    """Request schema for file processing operations."""
    file_id: str = Field(..., description="File ID to process")
    
    # Processing options
    generate_thumbnail: bool = Field(default=True, description="Generate thumbnail")
    extract_metadata: bool = Field(default=True, description="Extract metadata")
    create_preview: bool = Field(default=False, description="Create preview")
    optimize_file: bool = Field(default=False, description="Optimize file size")
    
    # Conversion options
    convert_format: Optional[str] = Field(default=None, description="Convert to format")
    resize_dimensions: Optional[Dict[str, int]] = Field(default=None, description="Resize dimensions")
    compress_quality: Optional[int] = Field(default=None, ge=1, le=100, description="Compression quality")
    
    # Security
    scan_for_viruses: bool = Field(default=True, description="Scan for viruses")
    validate_integrity: bool = Field(default=True, description="Validate file integrity")
    
    @validator('convert_format')
    def validate_convert_format(cls, v):
        """Validate conversion format."""
        if v is not None:
            valid_formats = ['jpg', 'png', 'pdf', 'docx', 'mp4', 'mp3']
            if v.lower() not in valid_formats:
                raise ValueError(f'Unsupported conversion format: {v}')
        return v
    
    @validator('resize_dimensions')
    def validate_resize_dimensions(cls, v):
        """Validate resize dimensions."""
        if v is not None:
            if 'width' not in v or 'height' not in v:
                raise ValueError('Resize dimensions must include width and height')
            if v['width'] <= 0 or v['height'] <= 0:
                raise ValueError('Dimensions must be positive')
        return v
    
    @validator('compress_quality')
    def validate_compress_quality(cls, v):
        """Validate compression quality."""
        if v is not None and (v < 1 or v > 100):
            raise ValueError('Compression quality must be between 1 and 100')
        return v

class FileProcessingResponse(BaseResponseSchema):
    """Response schema for file processing results."""
    processing_id: str = Field(description="Processing unique identifier")
    file_id: str = Field(description="File ID")
    status: str = Field(description="Processing status")
    
    # Processing results
    thumbnail_generated: bool = Field(description="Whether thumbnail was generated")
    metadata_extracted: bool = Field(description="Whether metadata was extracted")
    preview_created: bool = Field(description="Whether preview was created")
    file_optimized: bool = Field(description="Whether file was optimized")
    
    # Generated files
    thumbnail_path: Optional[str] = Field(default=None, description="Thumbnail file path")
    preview_path: Optional[str] = Field(default=None, description="Preview file path")
    optimized_path: Optional[str] = Field(default=None, description="Optimized file path")
    
    # Metadata
    extracted_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Extracted metadata")
    processing_time: float = Field(description="Processing time in seconds")
    processing_errors: Optional[List[str]] = Field(default=None, description="Processing errors")
    
    # Timestamps
    started_at: datetime = Field(description="Processing start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Processing completion timestamp")
