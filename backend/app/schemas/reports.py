"""
Report-related Pydantic Schemas

This module contains all Pydantic models for report operations including:
- Report creation and updates
- Report templates
- Report export requests
- Report responses and listings
- AI analysis requests
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum

from .common import BaseRequestSchema, BaseResponseSchema, SanitizedString, SanitizedHTML

# Report status types
class ReportStatus(str, Enum):
    """Report status enumeration."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"

# Report types
class ReportType(str, Enum):
    """Report type enumeration."""
    BUSINESS = "business"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    ANALYTICS = "analytics"
    CUSTOM = "custom"

# Export formats
class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    EXCEL = "xlsx"
    CSV = "csv"
    JSON = "json"
    XML = "xml"

# Report template types
class TemplateType(str, Enum):
    """Report template types."""
    WORD = "word"
    POWERPOINT = "powerpoint"
    EXCEL = "excel"
    HTML = "html"
    CUSTOM = "custom"

class ReportTemplateSchema(BaseModel):
    """Schema for report templates."""
    id: str = Field(description="Template unique identifier")
    name: SanitizedString = Field(description="Template name")
    description: Optional[SanitizedString] = Field(default=None, description="Template description")
    type: TemplateType = Field(description="Template type")
    
    # Template content
    content: Optional[Dict[str, Any]] = Field(default=None, description="Template content structure")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    sections: Optional[List[Dict[str, Any]]] = Field(default=None, description="Template sections")
    
    # Metadata
    version: str = Field(default="1.0.0", description="Template version")
    author: Optional[str] = Field(default=None, description="Template author")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    
    # Configuration
    is_active: bool = Field(default=True, description="Whether template is active")
    is_public: bool = Field(default=False, description="Whether template is publicly available")
    requires_permission: bool = Field(default=True, description="Whether permission is required to use")
    
    # File information
    file_path: Optional[str] = Field(default=None, description="Template file path")
    file_size: Optional[int] = Field(default=None, description="Template file size in bytes")
    checksum: Optional[str] = Field(default=None, description="Template file checksum")
    
    # Timestamps
    created_at: datetime = Field(description="Template creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Version must be in semantic versioning format (e.g., 1.0.0)')
        return v

class ReportCreateRequest(BaseRequestSchema):
    """Request schema for creating a new report."""
    title: SanitizedString = Field(..., min_length=1, max_length=200, description="Report title")
    description: Optional[SanitizedHTML] = Field(default=None, description="Report description")
    type: ReportType = Field(description="Report type")
    
    # Template and data
    template_id: str = Field(description="Report template ID")
    data_source: Dict[str, Any] = Field(description="Report data source")
    
    # Configuration
    status: ReportStatus = Field(default=ReportStatus.DRAFT, description="Initial report status")
    priority: str = Field(default="medium", regex="^(low|medium|high|urgent)$", description="Report priority")
    
    # Content and structure
    sections: Optional[List[Dict[str, Any]]] = Field(default=None, description="Report sections")
    custom_fields: Optional[Dict[str, Any]] = Field(default=None, description="Custom report fields")
    
    # Access control
    is_public: bool = Field(default=False, description="Whether the report is publicly accessible")
    allowed_users: Optional[List[str]] = Field(default=None, description="List of allowed user IDs")
    allowed_roles: Optional[List[str]] = Field(default=None, description="List of allowed roles")
    
    # Scheduling
    scheduled_date: Optional[datetime] = Field(default=None, description="Scheduled generation date")
    auto_refresh: bool = Field(default=False, description="Enable automatic refresh")
    refresh_interval: Optional[int] = Field(default=None, ge=1, description="Refresh interval in hours")
    
    # Notifications
    enable_notifications: bool = Field(default=True, description="Enable notifications")
    notify_users: Optional[List[str]] = Field(default=None, description="Users to notify")
    notify_roles: Optional[List[str]] = Field(default=None, description="Roles to notify")
    
    @validator('data_source')
    def validate_data_source(cls, v):
        """Validate data source structure."""
        if not isinstance(v, dict):
            raise ValueError('Data source must be a dictionary')
        if not v:
            raise ValueError('Data source cannot be empty')
        return v
    
    @validator('scheduled_date')
    def validate_scheduled_date(cls, v):
        """Validate scheduled date is in the future."""
        if v is not None and v <= datetime.utcnow():
            raise ValueError('Scheduled date must be in the future')
        return v

class ReportUpdateRequest(BaseRequestSchema):
    """Request schema for updating an existing report."""
    title: Optional[SanitizedString] = Field(default=None, min_length=1, max_length=200, description="Report title")
    description: Optional[SanitizedHTML] = Field(default=None, description="Report description")
    type: Optional[ReportType] = Field(default=None, description="Report type")
    
    # Template and data
    template_id: Optional[str] = Field(default=None, description="Report template ID")
    data_source: Optional[Dict[str, Any]] = Field(default=None, description="Report data source")
    
    # Configuration
    status: Optional[ReportStatus] = Field(default=None, description="Report status")
    priority: Optional[str] = Field(default=None, regex="^(low|medium|high|urgent)$", description="Report priority")
    
    # Content and structure
    sections: Optional[List[Dict[str, Any]]] = Field(default=None, description="Report sections")
    custom_fields: Optional[Dict[str, Any]] = Field(default=None, description="Custom report fields")
    
    # Access control
    is_public: Optional[bool] = Field(default=None, description="Whether the report is publicly accessible")
    allowed_users: Optional[List[str]] = Field(default=None, description="List of allowed user IDs")
    allowed_roles: Optional[List[str]] = Field(default=None, description="List of allowed roles")
    
    # Scheduling
    scheduled_date: Optional[datetime] = Field(default=None, description="Scheduled generation date")
    auto_refresh: Optional[bool] = Field(default=None, description="Enable automatic refresh")
    refresh_interval: Optional[int] = Field(default=None, ge=1, description="Refresh interval in hours")
    
    # Notifications
    enable_notifications: Optional[bool] = Field(default=None, description="Enable notifications")
    notify_users: Optional[List[str]] = Field(default=None, description="Users to notify")
    notify_roles: Optional[List[str]] = Field(default=None, description="Roles to notify")

class ReportExportRequest(BaseRequestSchema):
    """Request schema for exporting reports."""
    report_id: str = Field(description="Report ID to export")
    template_id: Optional[str] = Field(default=None, description="Template ID for export")
    
    # Export configuration
    formats: List[ExportFormat] = Field(..., min_items=1, description="Export formats")
    data_source: Optional[Dict[str, Any]] = Field(default=None, description="Override data source")
    
    # Export options
    include_metadata: bool = Field(default=True, description="Include report metadata")
    include_charts: bool = Field(default=True, description="Include charts and graphs")
    include_attachments: bool = Field(default=False, description="Include file attachments")
    
    # Quality settings
    quality: str = Field(default="standard", regex="^(draft|standard|high|print)$", description="Export quality")
    compression: bool = Field(default=True, description="Enable file compression")
    
    # Customization
    custom_styles: Optional[Dict[str, Any]] = Field(default=None, description="Custom styling options")
    custom_header: Optional[str] = Field(default=None, description="Custom header text")
    custom_footer: Optional[str] = Field(default=None, description="Custom footer text")
    
    @validator('formats')
    def validate_formats(cls, v):
        """Validate export formats."""
        if not v:
            raise ValueError('At least one export format must be specified')
        if len(v) != len(set(v)):
            raise ValueError('Export formats must be unique')
        return v

class AIAnalysisRequest(BaseRequestSchema):
    """Request schema for AI-powered report analysis."""
    report_id: str = Field(description="Report ID to analyze")
    
    # Analysis configuration
    analysis_type: str = Field(..., regex="^(insights|anomalies|trends|recommendations|summary)$", description="Type of analysis")
    language: str = Field(default="en", regex="^[a-z]{2}$", description="Analysis language")
    
    # Data scope
    data_range: Optional[Dict[str, Any]] = Field(default=None, description="Data range for analysis")
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific areas to focus on")
    
    # Output preferences
    detail_level: str = Field(default="standard", regex="^(basic|standard|detailed|comprehensive)$", description="Analysis detail level")
    include_visualizations: bool = Field(default=True, description="Include generated visualizations")
    include_recommendations: bool = Field(default=True, description="Include actionable recommendations")
    
    # AI model settings
    model_preference: Optional[str] = Field(default=None, description="Preferred AI model")
    creativity_level: float = Field(default=0.7, ge=0.0, le=1.0, description="AI creativity level")
    
    @validator('creativity_level')
    def validate_creativity_level(cls, v):
        """Validate creativity level range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Creativity level must be between 0.0 and 1.0')
        return v

class ReportResponse(BaseResponseSchema):
    """Response schema for report data."""
    id: str = Field(description="Report unique identifier")
    title: str = Field(description="Report title")
    description: Optional[str] = Field(default=None, description="Report description")
    type: ReportStatus = Field(description="Report type")
    
    # Template and data
    template_id: str = Field(description="Report template ID")
    template: Optional[ReportTemplateSchema] = Field(default=None, description="Template information")
    data_source: Dict[str, Any] = Field(description="Report data source")
    
    # Configuration
    status: ReportStatus = Field(description="Report status")
    priority: str = Field(description="Report priority")
    
    # Content and structure
    sections: Optional[List[Dict[str, Any]]] = Field(default=None, description="Report sections")
    custom_fields: Optional[Dict[str, Any]] = Field(default=None, description="Custom report fields")
    
    # Access control
    is_public: bool = Field(description="Whether the report is publicly accessible")
    allowed_users: Optional[List[str]] = Field(default=None, description="List of allowed user IDs")
    allowed_roles: Optional[List[str]] = Field(default=None, description="List of allowed roles")
    
    # Scheduling
    scheduled_date: Optional[datetime] = Field(default=None, description="Scheduled generation date")
    auto_refresh: bool = Field(description="Enable automatic refresh")
    refresh_interval: Optional[int] = Field(default=None, description="Refresh interval in hours")
    
    # Notifications
    enable_notifications: bool = Field(description="Enable notifications")
    notify_users: Optional[List[str]] = Field(default=None, description="Users to notify")
    notify_roles: Optional[List[str]] = Field(default=None, description="Roles to notify")
    
    # Metadata
    created_at: datetime = Field(description="Report creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    created_by: Optional[str] = Field(default=None, description="User who created the report")
    
    # Statistics
    view_count: int = Field(default=0, description="Number of views")
    export_count: int = Field(default=0, description="Number of exports")
    last_exported: Optional[datetime] = Field(default=None, description="Last export timestamp")
    
    # Generated content
    generated_content: Optional[Dict[str, Any]] = Field(default=None, description="Generated report content")
    export_urls: Optional[Dict[str, str]] = Field(default=None, description="Export file URLs")
    
    # AI analysis
    ai_analysis: Optional[Dict[str, Any]] = Field(default=None, description="AI analysis results")

class ReportListResponse(BaseResponseSchema):
    """Response schema for report listings."""
    reports: List[ReportResponse] = Field(description="List of reports")
    total: int = Field(description="Total number of reports")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    
    # Filtering and sorting
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Applied filters")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default=None, description="Sort order")
    
    # Summary statistics
    status_counts: Dict[str, int] = Field(description="Count of reports by status")
    type_counts: Dict[str, int] = Field(description="Count of reports by type")

class ReportExportResponse(BaseResponseSchema):
    """Response schema for report export results."""
    export_id: str = Field(description="Export unique identifier")
    report_id: str = Field(description="Report ID")
    status: str = Field(description="Export status")
    
    # Export results
    formats: List[ExportFormat] = Field(description="Requested export formats")
    urls: Dict[str, str] = Field(description="Export file URLs by format")
    file_info: Dict[str, Dict[str, Any]] = Field(description="File information by format")
    
    # Metadata
    exported_at: datetime = Field(description="Export timestamp")
    exported_by: Optional[str] = Field(default=None, description="User who initiated export")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    
    # Quality and settings
    quality: str = Field(description="Export quality used")
    compression: bool = Field(description="Compression applied")
    
    # Error handling
    errors: Optional[Dict[str, str]] = Field(default=None, description="Export errors by format")
    warnings: Optional[List[str]] = Field(default=None, description="Export warnings")

class AIAnalysisResponse(BaseResponseSchema):
    """Response schema for AI analysis results."""
    analysis_id: str = Field(description="Analysis unique identifier")
    report_id: str = Field(description="Report ID")
    analysis_type: str = Field(description="Type of analysis performed")
    
    # Analysis results
    insights: List[Dict[str, Any]] = Field(description="Key insights discovered")
    anomalies: Optional[List[Dict[str, Any]]] = Field(default=None, description="Anomalies detected")
    trends: Optional[List[Dict[str, Any]]] = Field(default=None, description="Trends identified")
    recommendations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Actionable recommendations")
    summary: str = Field(description="Analysis summary")
    
    # Generated content
    visualizations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Generated visualizations")
    charts: Optional[List[Dict[str, Any]]] = Field(default=None, description="Generated charts")
    
    # Metadata
    analyzed_at: datetime = Field(description="Analysis timestamp")
    model_used: str = Field(description="AI model used for analysis")
    confidence_score: float = Field(description="Analysis confidence score")
    processing_time: float = Field(description="Processing time in seconds")
    
    # Quality metrics
    data_quality_score: Optional[float] = Field(default=None, description="Data quality assessment")
    relevance_score: Optional[float] = Field(default=None, description="Relevance assessment")

class ReportSearchRequest(BaseRequestSchema):
    """Request schema for searching reports."""
    query: Optional[str] = Field(default=None, description="Search query")
    type: Optional[ReportType] = Field(default=None, description="Report type filter")
    status: Optional[ReportStatus] = Field(default=None, description="Status filter")
    created_by: Optional[str] = Field(default=None, description="Creator filter")
    template_id: Optional[str] = Field(default=None, description="Template filter")
    
    # Date range
    created_after: Optional[datetime] = Field(default=None, description="Created after date")
    created_before: Optional[datetime] = Field(default=None, description="Created before date")
    updated_after: Optional[datetime] = Field(default=None, description="Updated after date")
    updated_before: Optional[datetime] = Field(default=None, description="Updated before date")
    
    # Access control
    is_public: Optional[bool] = Field(default=None, description="Public/private filter")
    user_accessible: Optional[bool] = Field(default=None, description="User accessibility filter")
    
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
