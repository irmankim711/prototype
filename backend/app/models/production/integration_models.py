"""
Google Forms to Sheets Integration Models

This module contains the database models for managing Google Forms to Google Sheets
integration configurations, export history, and OAuth token management.
"""

from datetime import datetime
from enum import Enum
import uuid
from cryptography.fernet import Fernet
import os

from app import db


class IntegrationConfig(db.Model):
    """Model for managing Google Forms to Sheets integration configurations."""
    __tablename__ = 'integration_configs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Source Configuration
    google_form_id = db.Column(db.String(255), nullable=False)
    google_form_title = db.Column(db.String(255))
    
    # Destination Configuration
    google_sheet_id = db.Column(db.String(255))
    google_sheet_title = db.Column(db.String(255))
    sheet_tab_name = db.Column(db.String(255), default='Form Responses')
    
    # Export Settings
    export_mode = db.Column(db.Enum('create_new', 'update_existing', 'append_only', name='export_mode_enum'), default='append_only')
    include_timestamps = db.Column(db.Boolean, default=True)
    include_response_id = db.Column(db.Boolean, default=True)
    
    # Transformation Rules
    transformation_rules = db.Column(db.JSON)
    formatting_rules = db.Column(db.JSON)
    custom_headers = db.Column(db.JSON)
    
    # Scheduling
    schedule_enabled = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.Enum('hourly', 'daily', 'weekly', name='schedule_frequency_enum'), default='daily')
    schedule_time = db.Column(db.Time)
    last_export_at = db.Column(db.DateTime)
    next_export_at = db.Column(db.DateTime)
    
    # Status and Metadata
    status = db.Column(db.Enum('active', 'paused', 'error', name='integration_status_enum'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    export_history = db.relationship('ExportHistory', backref='integration', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """IntegrationConfig constructor"""
        super(IntegrationConfig, self).__init__(**kwargs)
    
    def to_dict(self):
        """Convert integration config to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'google_form_id': self.google_form_id,
            'google_form_title': self.google_form_title,
            'google_sheet_id': self.google_sheet_id,
            'google_sheet_title': self.google_sheet_title,
            'sheet_tab_name': self.sheet_tab_name,
            'export_mode': self.export_mode,
            'include_timestamps': self.include_timestamps,
            'include_response_id': self.include_response_id,
            'transformation_rules': self.transformation_rules,
            'formatting_rules': self.formatting_rules,
            'custom_headers': self.custom_headers,
            'schedule_enabled': self.schedule_enabled,
            'schedule_frequency': self.schedule_frequency,
            'schedule_time': self.schedule_time.isoformat() if self.schedule_time else None,
            'last_export_at': self.last_export_at.isoformat() if self.last_export_at else None,
            'next_export_at': self.next_export_at.isoformat() if self.next_export_at else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ExportHistory(db.Model):
    """Model for tracking Google Forms to Sheets export operations."""
    __tablename__ = 'export_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = db.Column(db.String(36), db.ForeignKey('integration_configs.id'), nullable=False)
    
    # Export Details
    export_type = db.Column(db.Enum('manual', 'scheduled', name='export_type_enum'), nullable=False)
    status = db.Column(db.Enum('pending', 'running', 'completed', 'failed', name='export_status_enum'), default='pending')
    
    # Data Statistics
    records_processed = db.Column(db.Integer, default=0)
    records_exported = db.Column(db.Integer, default=0)
    records_skipped = db.Column(db.Integer, default=0)
    
    # Timing Information
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Float)
    
    # Results and Errors
    result_sheet_url = db.Column(db.String(500))
    error_message = db.Column(db.Text)
    error_details = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        """ExportHistory constructor"""
        super(ExportHistory, self).__init__(**kwargs)
    
    def to_dict(self):
        """Convert export history to dictionary for API responses"""
        return {
            'id': self.id,
            'integration_id': self.integration_id,
            'export_type': self.export_type,
            'status': self.status,
            'records_processed': self.records_processed,
            'records_exported': self.records_exported,
            'records_skipped': self.records_skipped,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'result_sheet_url': self.result_sheet_url,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class OAuthTokens(db.Model):
    """Model for storing encrypted OAuth tokens for Google API access."""
    __tablename__ = 'oauth_tokens'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False, default='google')
    
    # Encrypted Token Information
    access_token = db.Column(db.Text, nullable=False)  # Encrypted
    refresh_token = db.Column(db.Text)  # Encrypted
    token_type = db.Column(db.String(50), default='Bearer')
    expires_at = db.Column(db.DateTime)
    
    # Scope Information
    scopes = db.Column(db.JSON)  # List of granted scopes
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        """OAuthTokens constructor"""
        super(OAuthTokens, self).__init__(**kwargs)
    
    @staticmethod
    def _get_encryption_key():
        """Get or create encryption key for token storage"""
        key = os.environ.get('OAUTH_ENCRYPTION_KEY')
        if not key:
            # Generate a new key if not set (for development)
            key = Fernet.generate_key().decode()
            os.environ['OAUTH_ENCRYPTION_KEY'] = key
        return key.encode() if isinstance(key, str) else key
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        if not token:
            return None
        f = Fernet(self._get_encryption_key())
        return f.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token for use"""
        if not encrypted_token:
            return None
        f = Fernet(self._get_encryption_key())
        return f.decrypt(encrypted_token.encode()).decode()
    
    def set_access_token(self, token: str):
        """Set encrypted access token"""
        self.access_token = self.encrypt_token(token)
    
    def get_access_token(self) -> str:
        """Get decrypted access token"""
        return self.decrypt_token(self.access_token)
    
    def set_refresh_token(self, token: str):
        """Set encrypted refresh token"""
        self.refresh_token = self.encrypt_token(token)
    
    def get_refresh_token(self) -> str:
        """Get decrypted refresh token"""
        return self.decrypt_token(self.refresh_token)
    
    def is_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    def to_dict(self, include_tokens=False):
        """Convert OAuth tokens to dictionary for API responses"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'scopes': self.scopes,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Only include actual tokens if explicitly requested (for internal use)
        if include_tokens:
            result.update({
                'access_token': self.get_access_token(),
                'refresh_token': self.get_refresh_token()
            })
        
        return result