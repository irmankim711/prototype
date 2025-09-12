"""
Safe ReportTemplate model that matches the actual database schema
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from datetime import datetime
from app import db

class SafeReportTemplate(db.Model):
    """Safe template model that matches actual database schema"""
    __tablename__ = 'report_templates'
    __table_args__ = {'extend_existing': True}
    
    # Columns that actually exist in the database
    id = Column(UUID(as_uuid=True), primary_key=True)
    organization_id = Column(UUID(as_uuid=True))
    category_id = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))
    name = Column(String, nullable=False)
    description = Column(Text)
    template_type = Column(String, nullable=False)
    content_template = Column(Text)
    data_sources = Column(JSONB)
    parameters = Column(JSONB)
    styling = Column(JSONB)
    chart_configs = Column(JSONB)
    is_public = Column(Boolean)
    usage_count = Column(Integer)
    tags = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
