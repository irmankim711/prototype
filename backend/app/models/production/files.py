"""
File Models for production deployment
NO MOCK DATA - Real file management
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app import db

class File(db.Model):
    """Real file model for managing uploaded files and documents - NO MOCK DATA"""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    uploader_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # File metadata
    description = Column(Text)
    tags = Column(JSON)  # Array of tags
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # File processing
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, error
    processing_error = Column(Text)
    processed_at = Column(DateTime)
    
    # Security
    access_key = Column(String(100))  # Unique access key for public files
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime)
    
    # Relationships - Commented out to avoid circular dependency issues
    # uploader = relationship("User", back_populates="files")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploader_id': self.uploader_id,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'description': self.description,
            'tags': self.tags,
            'is_public': self.is_public,
            'is_active': self.is_active,
            'processing_status': self.processing_status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'download_count': self.download_count,
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None
        }
