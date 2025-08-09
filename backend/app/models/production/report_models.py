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
    
    # Relationships
    reports = relationship("Report", back_populates="template")

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
    """Real report generation tracking - NO MOCK DATA"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    template_id = Column(Integer, ForeignKey('report_templates.id'), nullable=False)
    
    # Report metadata
    title = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(String(50))  # summary, detailed, attendance, evaluation
    
    # Generation status
    generation_status = Column(String(20), default='pending')  # pending, generating, completed, failed
    generated_at = Column(DateTime)
    generation_time_seconds = Column(Integer)  # Time taken to generate
    
    # File information
    file_path = Column(String(500))
    file_size = Column(Integer)  # File size in bytes
    file_format = Column(String(10))  # docx, pdf, xlsx
    download_url = Column(String(500))
    
    # Usage tracking
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime)
    
    # Generation data
    data_source = Column(JSON)  # Data used for generation
    generation_config = Column(JSON)  # Configuration used
    error_message = Column(Text)  # Error message if generation failed
    
    # Quality metrics
    completeness_score = Column(Integer)  # 0-100 based on data completeness
    processing_notes = Column(Text)
    
    # User tracking
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    program = relationship("Program")
    template = relationship("ReportTemplate", back_populates="reports")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'program_id': self.program_id,
            'template_id': self.template_id,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'generation_status': self.generation_status,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'generation_time_seconds': self.generation_time_seconds,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'download_url': self.download_url,
            'download_count': self.download_count,
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None,
            'completeness_score': self.completeness_score,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'error_message': self.error_message
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
