"""
Supabase-compatible Report model that matches the actual database schema
This avoids the schema mismatch issues completely
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .. import db

class SupabaseReport(db.Model):
    """Report model that matches the actual Supabase schema exactly"""
    __tablename__ = 'reports'
    
    # Primary key - UUID as in Supabase
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core report info
    title = Column(String, nullable=False)
    description = Column(Text)
    report_type = Column(String, nullable=False)
    status = Column(String, default='pending')  # This exists in Supabase
    
    # Organization and template references (UUIDs as in Supabase)
    organization_id = Column(UUID(as_uuid=True))
    template_id = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))
    
    # File information
    file_url = Column(Text)
    file_size = Column(Integer)
    file_format = Column(String)
    
    # Generation info
    generation_time = Column(Integer)  # This exists in Supabase
    error_message = Column(Text)
    
    # Metadata
    parameters = Column(JSON, default=dict)
    data_snapshot = Column(JSON)
    
    # Scheduling and expiry
    scheduled_for = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Usage tracking
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'status': self.status,
            'organization_id': str(self.organization_id) if self.organization_id else None,
            'template_id': str(self.template_id) if self.template_id else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'generation_time': self.generation_time,
            'error_message': self.error_message,
            'parameters': self.parameters,
            'data_snapshot': self.data_snapshot,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_status(self, status, error_message=None):
        """Update report status"""
        self.status = status
        if status == 'completed':
            self.completed_at = datetime.utcnow()
        elif status == 'failed' and error_message:
            self.error_message = error_message
    
    def increment_downloads(self):
        """Increment download count"""
        self.download_count = (self.download_count or 0) + 1
    
    def increment_views(self):
        """Increment view count"""
        self.view_count = (self.view_count or 0) + 1
    
    @classmethod
    def create_report(cls, title, report_type, description=None, template_id=None, 
                     organization_id=None, created_by=None, parameters=None):
        """Create a new report with proper defaults"""
        return cls(
            title=title,
            description=description,
            report_type=report_type,
            status='pending',
            template_id=template_id,
            organization_id=organization_id,
            created_by=created_by,
            parameters=parameters or {}
        )
    
    def __repr__(self):
        return f'<SupabaseReport {self.id}: {self.title}>'
