"""
Validation schemas and utilities for the backend API
Provides consistent validation acro    @validates('options')
    def validate_options(self, value, **kwargs):
        if value is not None:
            for option in value:
                if not isinstance(option, dict) or 'value' not in option or 'label' not in option:
                    raise ValidationError('Each option must have "value" and "label" fields') endpoints using Marshmallow
"""

from marshmallow import Schema, fields, validates, ValidationError, post_load
from marshmallow.validate import Length, Email, Range, OneOf, Regexp
from datetime import datetime
import re
from ..models import Form, User, FormSubmission
from flask import current_app


class BaseSchema(Schema):
    """Base schema with common validation utilities"""
    
    def handle_error(self, error, data, **kwargs):
        """Custom error handler for better error messages"""
        try:
            current_app.logger.warning(f"Validation error: {error}")
        except RuntimeError:
            # Handle case when running outside application context (e.g., tests)
            pass
        raise ValidationError(error.messages)


class UserRegistrationSchema(BaseSchema):
    """Schema for user registration validation"""
    
    email = fields.Email(required=True, validate=Length(max=120))
    password = fields.Str(required=True, validate=Length(min=8, max=128))
    first_name = fields.Str(validate=Length(max=50))
    last_name = fields.Str(validate=Length(max=50))
    username = fields.Str(validate=Length(min=3, max=50))
    phone = fields.Str(validate=Length(max=20))
    company = fields.Str(validate=Length(max=100))
    job_title = fields.Str(validate=Length(max=100))
    
    @validates('email')
    def validate_unique_email(self, value, **kwargs):
        try:
            if User.query.filter_by(email=value).first():
                raise ValidationError('Email address already registered')
        except RuntimeError:
            # Skip database validation when running outside app context (e.g., tests)
            pass
    
    @validates('username')
    def validate_unique_username(self, value, **kwargs):
        try:
            if value and User.query.filter_by(username=value).first():
                raise ValidationError('Username already taken')
        except RuntimeError:
            # Skip database validation when running outside app context (e.g., tests)
            pass
    
    @validates('password')
    def validate_password_strength(self, value, **kwargs):
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('Password must contain at least one special character')


class UserUpdateSchema(BaseSchema):
    """Schema for user profile updates"""
    
    first_name = fields.Str(validate=Length(max=50), allow_none=True)
    last_name = fields.Str(validate=Length(max=50), allow_none=True)
    phone = fields.Str(validate=Length(max=20), allow_none=True)
    company = fields.Str(validate=Length(max=100), allow_none=True)
    job_title = fields.Str(validate=Length(max=100), allow_none=True)
    bio = fields.Str(validate=Length(max=500), allow_none=True)
    timezone = fields.Str(validate=Length(max=50), allow_none=True)
    language = fields.Str(validate=OneOf(['en', 'es', 'fr', 'de', 'it']), allow_none=True)
    theme = fields.Str(validate=OneOf(['light', 'dark']), allow_none=True)
    email_notifications = fields.Bool()
    push_notifications = fields.Bool()


class FormFieldSchema(BaseSchema):
    """Schema for individual form field validation"""
    
    id = fields.Str(required=True)
    type = fields.Str(required=True, validate=OneOf([
        'text', 'textarea', 'email', 'number', 'tel', 'url', 'password',
        'date', 'time', 'datetime-local', 'checkbox', 'radio', 'select',
        'file', 'hidden', 'range', 'color'
    ]))
    label = fields.Str(required=True, validate=Length(min=1, max=200))
    placeholder = fields.Str(validate=Length(max=200), allow_none=True)
    required = fields.Bool(load_default=False)
    options = fields.List(fields.Dict(), allow_none=True)
    validation = fields.Dict(allow_none=True)
    default_value = fields.Raw(allow_none=True)
    description = fields.Str(validate=Length(max=500), allow_none=True)
    
    @validates('id')
    def validate_field_id(self, value, **kwargs):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            raise ValidationError('Field ID must start with a letter and contain only letters, numbers, and underscores')
    
    @validates('options')
    def validate_options(self, value):
        if value is not None:
            for option in value:
                if not isinstance(option, dict) or 'value' not in option or 'label' not in option:
                    raise ValidationError('Each option must have "value" and "label" properties')


class FormCreationSchema(BaseSchema):
    """Schema for form creation validation"""
    
    title = fields.Str(required=True, validate=Length(min=3, max=200))
    description = fields.Str(validate=Length(max=1000), allow_none=True)
    is_public = fields.Bool(load_default=False)
    is_active = fields.Bool(load_default=True)
    schema = fields.Dict(required=True)
    form_settings = fields.Dict(allow_none=True)
    submission_limit = fields.Int(validate=Range(min=1), allow_none=True)
    expires_at = fields.DateTime(allow_none=True)
    
    @validates('title')
    def validate_unique_title(self, value, **kwargs):
        # Check if form with same title exists for current user
        # This would need to be implemented with user context
        pass
    
    @validates('schema')
    def validate_form_schema(self, value, **kwargs):
        if not isinstance(value, dict):
            raise ValidationError('Schema must be a valid JSON object')
        
        if 'fields' not in value:
            raise ValidationError('Schema must contain a "fields" array')
        
        fields_data = value.get('fields', [])
        if not isinstance(fields_data, list) or len(fields_data) == 0:
            raise ValidationError('Schema must contain at least one field')
        
        # Validate each field
        field_schema = FormFieldSchema()
        field_ids = set()
        
        for field in fields_data:
            try:
                field_schema.load(field)
                
                # Check for duplicate field IDs
                field_id = field.get('id')
                if field_id in field_ids:
                    raise ValidationError(f'Duplicate field ID: {field_id}')
                field_ids.add(field_id)
                
            except ValidationError as e:
                raise ValidationError(f'Invalid field configuration: {e.messages}')
    
    @validates('expires_at')
    def validate_expiration_date(self, value, **kwargs):
        if value and value <= datetime.utcnow():
            raise ValidationError('Expiration date must be in the future')


class FormUpdateSchema(FormCreationSchema):
    """Schema for form updates - inherits from creation but makes fields optional"""
    
    title = fields.Str(validate=Length(min=3, max=200))
    schema = fields.Dict()


class FormSubmissionSchema(BaseSchema):
    """Schema for form submission validation"""
    
    data = fields.Dict(required=True)
    submitter_email = fields.Email(allow_none=True)
    
    def __init__(self, form_schema=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_schema = form_schema
    
    @validates('data')
    def validate_submission_data(self, value, **kwargs):
        if not self.form_schema:
            return  # Skip validation if no form schema provided
        
        form_fields = self.form_schema.get('fields', [])
        field_configs = {field['id']: field for field in form_fields}
        
        # Check required fields
        for field in form_fields:
            field_id = field['id']
            is_required = field.get('required', False)
            
            if is_required and (field_id not in value or not value[field_id]):
                raise ValidationError(f'Field "{field.get("label", field_id)}" is required')
        
        # Validate field types and values
        for field_id, field_value in value.items():
            if field_id not in field_configs:
                continue  # Skip unknown fields
            
            field_config = field_configs[field_id]
            field_type = field_config['type']
            
            # Type-specific validation
            self._validate_field_value(field_id, field_value, field_config)
    
    def _validate_field_value(self, field_id, value, field_config):
        """Validate individual field values based on type"""
        field_type = field_config['type']
        field_label = field_config.get('label', field_id)
        
        if value is None or value == '':
            return  # Skip validation for empty values (required check is separate)
        
        try:
            if field_type == 'email':
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)):
                    raise ValidationError(f'{field_label} must be a valid email address')
            
            elif field_type == 'number':
                float(value)  # Will raise ValueError if not a number
            
            elif field_type == 'tel':
                if not re.match(r'^\+?[\d\s\-\(\)]+$', str(value)):
                    raise ValidationError(f'{field_label} must be a valid phone number')
            
            elif field_type == 'url':
                if not re.match(r'^https?://.+', str(value)):
                    raise ValidationError(f'{field_label} must be a valid URL')
            
            elif field_type in ['text', 'textarea']:
                validation_rules = field_config.get('validation', {})
                
                if 'minLength' in validation_rules:
                    min_length = validation_rules['minLength']
                    if len(str(value)) < min_length:
                        raise ValidationError(f'{field_label} must be at least {min_length} characters')
                
                if 'maxLength' in validation_rules:
                    max_length = validation_rules['maxLength']
                    if len(str(value)) > max_length:
                        raise ValidationError(f'{field_label} cannot exceed {max_length} characters')
                
                if 'pattern' in validation_rules:
                    pattern = validation_rules['pattern']
                    if not re.match(pattern, str(value)):
                        raise ValidationError(f'{field_label} format is invalid')
            
            elif field_type == 'select' or field_type == 'radio':
                options = field_config.get('options', [])
                valid_values = [opt['value'] for opt in options]
                if value not in valid_values:
                    raise ValidationError(f'{field_label} must be one of: {", ".join(valid_values)}')
        
        except ValueError:
            raise ValidationError(f'{field_label} must be a valid {field_type}')


class ReportCreationSchema(BaseSchema):
    """Schema for report creation validation"""
    
    title = fields.Str(required=True, validate=Length(min=3, max=120))
    description = fields.Str(validate=Length(max=500), allow_none=True)
    template_id = fields.Str(validate=Length(max=120), allow_none=True)
    data = fields.Dict(allow_none=True)
    
    @validates('template_id')
    def validate_template_id(self, value, **kwargs):
        if value and value not in ['form_analysis', 'generic', 'custom']:
            raise ValidationError('Invalid template ID')


# Validation utility functions
class ValidationUtils:
    """Utility functions for common validation tasks"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove potentially harmful HTML/script content"""
        import bleach
        return bleach.clean(text, tags=[], strip=True)
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions=None, max_size_mb=10):
        """Validate uploaded files"""
        if not file:
            raise ValidationError('No file provided')
        
        if allowed_extensions:
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext not in allowed_extensions:
                raise ValidationError(f'File type not allowed. Allowed: {", ".join(allowed_extensions)}')
        
        # Check file size (approximate)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValidationError(f'File size cannot exceed {max_size_mb}MB')
    
    @staticmethod
    def validate_json_structure(data, required_keys=None):
        """Validate JSON structure has required keys"""
        if not isinstance(data, dict):
            raise ValidationError('Data must be a valid JSON object')
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                raise ValidationError(f'Missing required keys: {", ".join(missing_keys)}')
    
    @staticmethod
    def validate_pagination_params(page, per_page, max_per_page=100):
        """Validate pagination parameters"""
        try:
            page = int(page) if page else 1
            per_page = int(per_page) if per_page else 20
        except ValueError:
            raise ValidationError('Page and per_page must be integers')
        
        if page < 1:
            raise ValidationError('Page must be greater than 0')
        
        if per_page < 1 or per_page > max_per_page:
            raise ValidationError(f'Per page must be between 1 and {max_per_page}')
        
        return page, per_page
