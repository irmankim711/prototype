"""
Report Models for production deployment
NO MOCK DATA - All reports generated from real data
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app import db

class ReportTemplate(db.Model):
    """Real report templates - NO MOCK DATA"""
    __tablename__ = 'report_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False)  # docx, pdf, excel, html
    file_path = Column(String(500), nullable=False)  # Path to template file
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
    
    # Relationships removed due to schema mismatch

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
    """Real report generation tracking - matches actual database schema exactly"""
    __tablename__ = 'reports'
    
    # ONLY columns that exist in the actual database
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer)
    template_id = Column(Integer)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(String(50))
    generation_status = Column(String(20))
    generated_at = Column(DateTime)
    generation_time_seconds = Column(Integer)
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_format = Column(String(10))
    download_url = Column(String(500))
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime)
    data_source = Column(JSON)
    generation_config = Column(JSON)
    error_message = Column(Text)
    completeness_score = Column(Integer)
    processing_notes = Column(Text)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add computed properties for compatibility
    @property
    def status(self):
        """Map generation_status to status for backward compatibility."""
        return self.generation_status or 'pending'
    
    @status.setter
    def status(self, value):
        """Set generation_status when status is set."""
        self.generation_status = value
    
    @property
    def user_id(self):
        """Extract user_id from created_by for compatibility."""
        if self.created_by and self.created_by.isdigit():
            return int(self.created_by)
        return None
    
    @user_id.setter
    def user_id(self, value):
        """Set created_by when user_id is set."""
        if value:
            self.created_by = str(value)

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'program_id': self.program_id,
            'template_id': self.template_id,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'status': self.status,  # Computed property
            'generation_status': self.generation_status,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'generation_time_seconds': self.generation_time_seconds,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'download_url': self.download_url,
            'download_count': self.download_count,
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None,
            'data_source': self.data_source,
            'generation_config': self.generation_config,
            'error_message': self.error_message,
            'completeness_score': self.completeness_score,
            'processing_notes': self.processing_notes,
            'created_by': self.created_by,
            'user_id': self.user_id,  # Computed property
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def update_generation_status(self, status, error_message=None, file_path=None, file_size=None):
        """Update report generation status"""
        self.generation_status = status
        
        if status == 'completed':
            self.generated_at = datetime.utcnow()
            if file_path:
                self.file_path = file_path
            if file_size:
                self.file_size = file_size
        elif status == 'failed' and error_message:
            self.error_message = error_message
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count = (self.download_count or 0) + 1
        self.last_downloaded = datetime.utcnow()

class ReportAnalytics(db.Model):
    """Report analytics and insights - NO MOCK DATA"""
    __tablename__ = 'report_analytics'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Analytics data
    participant_statistics = Column(JSON)  # Participant-related stats
    attendance_statistics = Column(JSON)  # Attendance-related stats
    program_effectiveness = Column(JSON)  # Program effectiveness metrics
    ai_insights = Column(JSON)  # AI-generated insights
    
    # Temporal analysis
    response_patterns = Column(JSON)  # Response time patterns
    engagement_metrics = Column(JSON)  # Engagement analysis
    
    # Quality metrics
    data_quality_score = Column(Integer)  # Overall data quality (0-100)
    completeness_percentage = Column(Integer)  # Data completeness (0-100)
    reliability_score = Column(Integer)  # Data reliability (0-100)
    
    # Generated insights
    key_findings = Column(JSON)  # Key findings from analysis
    recommendations = Column(JSON)  # Recommendations
    action_items = Column(JSON)  # Suggested action items
    
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
