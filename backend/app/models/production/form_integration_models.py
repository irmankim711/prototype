"""
Form Integration Models for production deployment
NO MOCK DATA - All integrations use real API data
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app import db

class FormIntegration(db.Model):
    """Real form integration tracking - NO MOCK DATA"""
    __tablename__ = 'form_integrations'
    
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    platform = Column(String(50), nullable=False)  # google_forms, microsoft_forms
    form_id = Column(String(255), nullable=False)
    form_title = Column(String(255))
    form_url = Column(String(500))
    integration_status = Column(String(20), default='active')  # active, inactive, error
    last_sync = Column(DateTime)
    sync_count = Column(Integer, default=0)
    error_message = Column(Text)
    configuration = Column(JSON)  # Platform-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))  # User who created the integration
    
    # API-specific configuration
    oauth_user_id = Column(String(255))  # User ID for OAuth
    webhook_url = Column(String(500))  # Webhook endpoint if available
    sync_frequency = Column(String(20), default='manual')  # manual, hourly, daily
    
    # Relationships
    program = relationship("Program", back_populates="form_integrations")
    form_responses = relationship("FormResponse", back_populates="integration", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'program_id': self.program_id,
            'platform': self.platform,
            'form_id': self.form_id,
            'form_title': self.form_title,
            'form_url': self.form_url,
            'integration_status': self.integration_status,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_count': self.sync_count,
            'error_message': self.error_message,
            'configuration': self.configuration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sync_frequency': self.sync_frequency,
            'response_count': len(self.form_responses) if self.form_responses else 0
        }

class FormResponse(db.Model):
    """Real form response storage - NO MOCK DATA"""
    __tablename__ = 'form_responses'
    
    id = Column(Integer, primary_key=True)
    integration_id = Column(Integer, ForeignKey('form_integrations.id'), nullable=False)
    external_response_id = Column(String(255), nullable=False)  # ID from external platform
    
    # Response data
    response_data = Column(JSON, nullable=False)  # Raw response data from platform
    normalized_data = Column(JSON)  # Normalized data for easier processing
    
    # Metadata
    submitted_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(20), default='pending')  # pending, processed, error
    processing_error = Column(Text)
    
    # Participant mapping
    participant_id = Column(Integer, ForeignKey('participants.id'))  # If mapped to participant
    
    # Quality metrics
    completion_score = Column(Integer)  # 0-100 based on completeness
    data_quality_score = Column(Integer)  # 0-100 based on data quality
    
    # Relationships
    integration = relationship("FormIntegration", back_populates="form_responses")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'integration_id': self.integration_id,
            'external_response_id': self.external_response_id,
            'response_data': self.response_data,
            'normalized_data': self.normalized_data,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processing_status': self.processing_status,
            'participant_id': self.participant_id,
            'completion_score': self.completion_score,
            'data_quality_score': self.data_quality_score
        }

    def normalize_response_data(self):
        """Normalize response data for easier processing"""
        if not self.response_data:
            return
        
        # Standard field mapping
        field_mapping = {
            'name': ['name', 'full name', 'participant name', 'nama', 'full_name'],
            'email': ['email', 'email address', 'e-mail', 'emel'],
            'phone': ['phone', 'phone number', 'mobile', 'telefon', 'contact'],
            'ic': ['ic', 'nric', 'identification', 'id number', 'identity'],
            'gender': ['gender', 'jantina', 'sex'],
            'organization': ['organization', 'company', 'organisasi', 'syarikat'],
            'position': ['position', 'job title', 'jawatan', 'title'],
            'department': ['department', 'jabatan', 'unit']
        }
        
        normalized = {}
        
        # Extract from response data
        answers = self.response_data.get('answers', {})
        
        for standard_field, possible_keys in field_mapping.items():
            for answer_key, answer_value in answers.items():
                if any(key.lower() in str(answer_key).lower() for key in possible_keys):
                    normalized[standard_field] = str(answer_value) if answer_value else None
                    break
        
        self.normalized_data = normalized
        
        # Calculate completion score
        self.completion_score = self._calculate_completion_score()
        self.data_quality_score = self._calculate_quality_score()

    def _calculate_completion_score(self):
        """Calculate completion score based on filled fields"""
        if not self.response_data:
            return 0
        
        answers = self.response_data.get('answers', {})
        if not answers:
            return 0
        
        total_fields = len(answers)
        completed_fields = len([v for v in answers.values() if v and str(v).strip()])
        
        return int((completed_fields / total_fields) * 100) if total_fields > 0 else 0

    def _calculate_quality_score(self):
        """Calculate data quality score"""
        if not self.normalized_data:
            return 0
        
        quality_score = 0
        total_checks = 0
        
        # Check email format
        if self.normalized_data.get('email'):
            total_checks += 1
            if '@' in self.normalized_data['email']:
                quality_score += 1
        
        # Check name length
        if self.normalized_data.get('name'):
            total_checks += 1
            if len(self.normalized_data['name']) > 2:
                quality_score += 1
        
        # Check IC format (Malaysian format)
        if self.normalized_data.get('ic'):
            total_checks += 1
            ic = str(self.normalized_data['ic']).replace('-', '').replace(' ', '')
            if len(ic) == 12 and ic.isdigit():
                quality_score += 1
        
        # Check phone format
        if self.normalized_data.get('phone'):
            total_checks += 1
            phone = str(self.normalized_data['phone']).replace('-', '').replace(' ', '').replace('+', '')
            if len(phone) >= 10 and phone.isdigit():
                quality_score += 1
        
        return int((quality_score / total_checks) * 100) if total_checks > 0 else 50
