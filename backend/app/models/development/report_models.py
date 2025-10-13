"""
Development Report Models
SQLite-compatible models for local development
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app import db

class ReportTemplate(db.Model):
    """Development report templates - SQLite compatible"""
    __tablename__ = 'report_templates'
    
    id = Column(Integer, primary_key=True)  # Auto-increment integer for SQLite
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False)  # docx, pdf, excel, html
    file_path = Column(String(500))  # Path to template file
    placeholder_schema = Column(JSON)  # Schema defining available placeholders
    category = Column(String(100))  # training, evaluation, certificate, etc.
    
    # Template metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default='1.0')
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # Template configuration
    supports_charts = Column(Boolean, default=False)
    supports_images = Column(Boolean, default=False)
    max_participants = Column(Integer)  # Max participants this template can handle

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'category': self.category,
            'placeholder_schema': self.placeholder_schema,
            'supports_charts': self.supports_charts,
            'supports_images': self.supports_images,
            'max_participants': self.max_participants,
            'usage_count': self.usage_count,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Report(db.Model):
    """Development report model - SQLite compatible with auto-increment IDs"""
    __tablename__ = 'reports'
    
    # Core fields - SQLite compatible
    id = Column(Integer, primary_key=True)  # Auto-increment integer for SQLite
    organization_id = Column(Integer)  # Reference to organization
    template_id = Column(Integer, ForeignKey('report_templates.id'))  # FK to templates
    created_by = Column(Integer)  # User ID who created the report
    title = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(String(50))
    status = Column(String(20), default='pending')  # 'pending', 'completed', 'failed', etc.
    parameters = Column(JSON)
    data_snapshot = Column(JSON)
    download_url = Column(Text)
    file_size = Column(Integer)
    file_format = Column(String(10))
    generation_time = Column(Integer)
    error_message = Column(Text)
    scheduled_for = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    program_id = Column(Integer)  # Reference to program
    generation_status = Column(String(20), default='pending')
    generated_at = Column(DateTime)
    file_path = Column(String(500))
    data_source = Column(JSON)  # JSON field for source data
    generation_config = Column(JSON)  # JSON field for generation config
    generation_time_seconds = Column(Integer)
    completeness_score = Column(Integer)
    processing_notes = Column(Text)
    last_downloaded = Column(DateTime)
    user_id = Column(Integer, nullable=False)  # User who owns this report

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'template_id': self.template_id,
            'created_by': self.created_by,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'status': self.status,
            'generation_status': self.generation_status,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'generation_time_seconds': self.generation_time_seconds,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'download_url': self.download_url,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None,
            'completeness_score': self.completeness_score,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'error_message': self.error_message,
            'user_id': self.user_id
        }

    def update_generation_status(self, status, error_message=None, file_path=None, file_size=None):
        """Update report generation status"""
        self.generation_status = status
        self.status = status  # Keep both in sync
        
        if status == 'completed':
            self.generated_at = datetime.utcnow()
            self.completed_at = datetime.utcnow()
            if file_path:
                self.file_path = file_path
            if file_size:
                self.file_size = file_size
        elif status == 'failed' and error_message:
            self.error_message = error_message
        
        self.updated_at = datetime.utcnow()
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count = (self.download_count or 0) + 1
        self.last_downloaded = datetime.utcnow()

class ReportAnalytics(db.Model):
    """Report analytics for development - SQLite compatible"""
    __tablename__ = 'report_analytics'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Analytics data
    participant_statistics = Column(JSON)
    attendance_statistics = Column(JSON)
    program_effectiveness = Column(JSON)
    ai_insights = Column(JSON)
    
    # Temporal analysis
    response_patterns = Column(JSON)
    engagement_metrics = Column(JSON)
    
    # Quality metrics
    data_quality_score = Column(Integer)
    completeness_percentage = Column(Integer)
    reliability_score = Column(Integer)
    
    # Generated insights
    key_findings = Column(JSON)
    recommendations = Column(JSON)
    action_items = Column(JSON)
    
    # Metadata
    analysis_date = Column(DateTime, default=datetime.utcnow)
    analysis_version = Column(String(20), default='1.0')
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'report_id': self.report_id,
            'participant_statistics': self.participant_statistics,
            'attendance_statistics': self.attendance_statistics,
            'program_effectiveness': self.program_effectiveness,
            'ai_insights': self.ai_insights,
            'response_patterns': self.response_patterns,
            'engagement_metrics': self.engagement_metrics,
            'data_quality_score': self.data_quality_score,
            'completeness_percentage': self.completeness_percentage,
            'reliability_score': self.reliability_score,
            'key_findings': self.key_findings,
            'recommendations': self.recommendations,
            'action_items': self.action_items,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'analysis_version': self.analysis_version
        }