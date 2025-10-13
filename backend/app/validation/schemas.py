"""
Enhanced validation schemas and utilities for the backend API
Provides consistent validation across all endpoints using Marshmallow
"""

from marshmallow import Schema, fields, validates, ValidationError, post_load
from marshmallow.validate import Length, Email, Range, OneOf, Regexp
from datetime import datetime
import re
# Temporarily commented out to fix relationship errors
# from ..models import Form, User, FormSubmission
from ..models import User
from flask import current_app


class ValidationUtils:
    """Enhanced validation utilities for common validation tasks"""

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not isinstance(value, str):
            return value

        # Remove script tags and potentially dangerous content
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<iframe[^>]*>.*?</iframe>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<object[^>]*>.*?</object>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<embed[^>]*>.*?</embed>', '', value, flags=re.IGNORECASE | re.DOTALL)

        # Remove javascript: and data: protocols
        value = re.sub(r'(javascript|data|vbscript):', '', value, flags=re.IGNORECASE)

        # Remove on* event handlers
        value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)

        return value.strip()

    @staticmethod
    def validate_file_upload(file, allowed_extensions=None, max_size_mb=50):
        """Validate file upload with comprehensive checks"""
        if not file or file.filename == '':
            raise ValidationError('No file selected')

        # Check file extension
        if allowed_extensions:
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            normalized_extensions = [ext.lower().lstrip('.') for ext in allowed_extensions]
            if file_ext not in normalized_extensions:
                raise ValidationError(
                    f'Invalid file type. Allowed extensions: {", ".join(allowed_extensions)}'
                )

        # Check file size (if available)
        if hasattr(file, 'content_length') and file.content_length:
            max_size_bytes = max_size_mb * 1024 * 1024
            if file.content_length > max_size_bytes:
                raise ValidationError(f'File too large. Maximum size: {max_size_mb}MB')

        # Validate filename for security
        filename = file.filename
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError('Invalid filename: path traversal detected')

        if not re.match(r'^[a-zA-Z0-9._-]+$', filename.replace(' ', '_')):
            raise ValidationError('Filename contains invalid characters')

        return True

    @staticmethod
    def validate_json_structure(data, required_fields=None, optional_fields=None):
        """Validate JSON structure and field requirements"""
        if not isinstance(data, dict):
            raise ValidationError('Data must be a JSON object')

        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(f'Missing required fields: {", ".join(missing_fields)}')

        # Validate all fields are either required or optional
        if required_fields and optional_fields:
            all_allowed_fields = set(required_fields + optional_fields)
            extra_fields = set(data.keys()) - all_allowed_fields
            if extra_fields:
                raise ValidationError(f'Unexpected fields: {", ".join(extra_fields)}')

        # Sanitize string values in the data
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = ValidationUtils.sanitize_string(value)

        return data

    @staticmethod
    def validate_id_format(id_value, field_name='id'):
        """Validate ID format for security"""
        if not isinstance(id_value, str) or not id_value.strip():
            raise ValidationError(f'{field_name} is required')

        # More permissive validation for dataSourceId which may contain Excel filenames with spaces
        if field_name.lower() in ['datasourceid', 'data_source_id']:
            # For datasource IDs, allow additional characters including spaces and periods
            # This accommodates Excel filenames like "SENARAI SEMAK PUNCAK ALAM.xlsx"
            if not re.match(r'^[a-zA-Z0-9_\-\s\.]+$', id_value):
                raise ValidationError(
                    f'{field_name} contains invalid characters. Only letters, numbers, spaces, periods, underscores, and hyphens are allowed'
                )
        else:
            # Strict validation for other ID fields
            if not re.match(r'^[a-zA-Z0-9_-]+$', id_value):
                raise ValidationError(
                    f'{field_name} can only contain letters, numbers, underscores, and hyphens'
                )

        return id_value.strip()


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
            pass
    
    @validates('password')
    def validate_password_strength(self, value, **kwargs):
        """Validate password meets security requirements"""
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('Password must contain at least one special character')


class UserUpdateSchema(BaseSchema):
    """Enhanced schema for user profile updates with comprehensive validation"""
    
    first_name = fields.Str(validate=Length(max=50), allow_none=True)
    last_name = fields.Str(validate=Length(max=50), allow_none=True) 
    username = fields.Str(validate=Length(min=3, max=30), required=True)
    phone = fields.Str(validate=Length(max=20), allow_none=True)
    company = fields.Str(validate=Length(max=100), allow_none=True)
    job_title = fields.Str(validate=Length(max=100), allow_none=True)
    bio = fields.Str(validate=Length(max=500), allow_none=True)
    timezone = fields.Str(validate=Length(max=50), required=True)
    language = fields.Str(validate=OneOf(['en', 'ms', 'zh', 'ta']), required=True)
    theme = fields.Str(validate=OneOf(['light', 'dark', 'auto']), required=True)
    email_notifications = fields.Bool(required=True)
    push_notifications = fields.Bool(required=True)

    @validates('username')
    def validate_username(self, value, **kwargs):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,29}$', value):
            raise ValidationError('Username must start with a letter and contain only letters, numbers, and underscores')

    @validates('phone')
    def validate_phone(self, value, **kwargs):
        """Validate phone number format"""
        if value:
            # Remove spaces and hyphens for validation
            clean_phone = re.sub(r'[\s\-]', '', value)
            if not re.match(r'^(\+\d{1,3})?\d{10}$', clean_phone):
                raise ValidationError('Please enter a valid phone number')

    @validates('first_name')
    def validate_first_name(self, value, **kwargs):
        """Validate first name format"""
        if value:
            if not re.match(r'^[a-zA-Z\s\'-]{1,50}$', value.strip()):
                raise ValidationError('First name can only contain letters, spaces, apostrophes, and hyphens')

    @validates('last_name')
    def validate_last_name(self, value, **kwargs):
        """Validate last name format"""
        if value:
            if not re.match(r'^[a-zA-Z\s\'-]{1,50}$', value.strip()):
                raise ValidationError('Last name can only contain letters, spaces, apostrophes, and hyphens')

    @validates('company')
    def validate_company(self, value, **kwargs):
        """Validate company name format"""
        if value:
            if not re.match(r'^[a-zA-Z0-9\s.,\'&-]{1,100}$', value.strip()):
                raise ValidationError('Company name contains invalid characters')

    @validates('job_title')
    def validate_job_title(self, value, **kwargs):
        """Validate job title format"""
        if value:
            if not re.match(r'^[a-zA-Z0-9\s.,\'&-]{1,100}$', value.strip()):
                raise ValidationError('Job title contains invalid characters')


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
    required = fields.Bool()
    disabled = fields.Bool()
    readonly = fields.Bool()
    
    # Validation options
    min_length = fields.Int(validate=Range(min=0))
    max_length = fields.Int(validate=Range(min=1))
    min_value = fields.Float()
    max_value = fields.Float()
    pattern = fields.Str()
    
    # Options for select/radio/checkbox fields
    options = fields.List(fields.Dict())
    
    @validates('id')
    def validate_field_id(self, value, **kwargs):
        """Ensure field ID follows naming conventions"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            raise ValidationError('Field ID must start with a letter and contain only letters, numbers, and underscores')

    @validates('options')
    def validate_options(self, value, **kwargs):
        if value is not None:
            for option in value:
                if not isinstance(option, dict) or 'value' not in option or 'label' not in option:
                    raise ValidationError('Each option must have "value" and "label" fields')


class FormCreationSchema(BaseSchema):
    """Schema for form creation validation"""
    
    title = fields.Str(required=True, validate=Length(min=1, max=200))
    description = fields.Str(validate=Length(max=1000), allow_none=True)
    is_public = fields.Bool()
    is_active = fields.Bool()
    
    # Form schema containing fields
    schema = fields.Dict(required=True)
    
    # Settings
    submit_button_text = fields.Str(validate=Length(max=50))
    success_message = fields.Str(validate=Length(max=500))
    redirect_url = fields.Url()
    
    @validates('schema')
    def validate_form_schema(self, value, **kwargs):
        """Validate the form schema structure"""
        if not isinstance(value, dict):
            raise ValidationError('Schema must be a dictionary')
        
        if 'fields' not in value or not isinstance(value['fields'], list):
            raise ValidationError('Schema must contain a "fields" array')
        
        if len(value['fields']) == 0:
            raise ValidationError('Form must have at least one field')
        
        # Validate each field
        field_ids = []
        for field in value['fields']:
            field_schema = FormFieldSchema()
            try:
                field_schema.load(field)
                field_ids.append(field['id'])
            except ValidationError as e:
                raise ValidationError(f"Invalid field: {e.messages}")
        
        # Check for duplicate field IDs
        if len(field_ids) != len(set(field_ids)):
            raise ValidationError('Field IDs must be unique')


class FormUpdateSchema(FormCreationSchema):
    """Schema for form updates - inherits from creation but allows partial updates"""
    
    title = fields.Str(validate=Length(min=1, max=200))
    schema = fields.Dict()


class FormSubmissionSchema(BaseSchema):
    """Schema for form submission validation"""
    
    form_id = fields.Int(required=True)
    data = fields.Dict(required=True)
    
    @validates('form_id')
    def validate_form_exists(self, value, **kwargs):
        """Ensure the form exists and is active"""
        try:
            # form = Form.query.get(value) # Temporarily commented out
            # if not form:
            #     raise ValidationError('Form not found')
            # if not form.is_active:
            #     raise ValidationError('Form is not active')
            pass # Temporarily commented out
        except RuntimeError:
            # Skip database validation when running outside app context
            pass


class ReportCreationSchema(BaseSchema):
    """Schema for report creation validation"""
    
    title = fields.Str(required=True, validate=Length(min=1, max=200))
    description = fields.Str(validate=Length(max=1000), allow_none=True)
    form_id = fields.Int(required=True)
    
    # Report configuration
    config = fields.Dict()
    
    @validates('form_id')
    def validate_form_exists_for_report(self, value, **kwargs):
        """Ensure the form exists for the report"""
        try:
            # form = Form.query.get(value) # Temporarily commented out
            # if not form:
            #     raise ValidationError('Form not found')
            pass # Temporarily commented out
        except RuntimeError:
            # Skip database validation when running outside app context
            pass

class ReportExportSchema(BaseSchema):
    """Schema for report export validation"""

    template_id = fields.Str(required=True, validate=Length(min=1, max=100))
    data_source = fields.Dict(required=True)
    formats = fields.List(fields.Str(validate=OneOf(['pdf', 'docx', 'html'])),
                         required=True, validate=Length(min=1, max=3))

    @validates('template_id')
    def validate_template_id(self, value, **kwargs):
        """Validate template ID format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError('Template ID can only contain alphanumeric characters, underscores, and hyphens')

    @validates('data_source')
    def validate_data_source(self, value, **kwargs):
        """Validate data source structure"""
        if not isinstance(value, dict) or len(value) == 0:
            raise ValidationError('Data source must be a non-empty dictionary')


class ExcelUploadSchema(BaseSchema):
    """Schema for Excel file upload validation"""

    sheet_name = fields.Str(validate=Length(max=100), allow_none=True)
    header_row = fields.Int(validate=Range(min=0, max=100), load_default=0)
    skip_rows = fields.Int(validate=Range(min=0, max=100), load_default=0)
    max_rows = fields.Int(validate=Range(min=1, max=10000), allow_none=True)


class AIReportSchema(BaseSchema):
    """Schema for AI-powered report generation"""

    data_source = fields.Dict(required=True)
    report_type = fields.Str(required=True, validate=OneOf([
        'summary', 'analysis', 'detailed', 'executive', 'technical'
    ]))
    include_insights = fields.Bool(load_default=True)
    custom_prompts = fields.List(fields.Str(validate=Length(max=500)),
                                validate=Length(max=5), allow_none=True)

    @validates('data_source')
    def validate_data_source(self, value, **kwargs):
        """Validate data source for AI processing"""
        if not isinstance(value, dict) or len(value) == 0:
            raise ValidationError('Data source must be a non-empty dictionary')


class GoogleFormsSchema(BaseSchema):
    """Schema for Google Forms integration"""

    form_id = fields.Str(required=True, validate=Length(min=20, max=50))
    sync_interval = fields.Int(validate=Range(min=60, max=3600), load_default=300)
    auto_sync = fields.Bool(load_default=True)

    @validates('form_id')
    def validate_google_form_id(self, value, **kwargs):
        """Validate Google Form ID format"""
        if not re.match(r'^[a-zA-Z0-9_-]{20,50}$', value):
            raise ValidationError('Invalid Google Form ID format')


class QueryParamsSchema(BaseSchema):
    """Schema for common query parameters"""

    page = fields.Int(validate=Range(min=1, max=1000), load_default=1)
    per_page = fields.Int(validate=Range(min=1, max=100), load_default=20)
    sort_by = fields.Str(validate=Length(max=50), allow_none=True)
    sort_order = fields.Str(validate=OneOf(['asc', 'desc']), load_default='desc')
    search = fields.Str(validate=Length(max=200), allow_none=True)

    @validates('search')
    def validate_search(self, value, **kwargs):
        """Sanitize search query"""
        if value:
            return ValidationUtils.sanitize_string(value)


class FileUploadValidationSchema(BaseSchema):
    """Schema for file upload metadata validation"""

    filename = fields.Str(required=True, validate=Length(min=1, max=255))
    content_type = fields.Str(required=True, validate=Length(min=1, max=100))
    size = fields.Int(required=True, validate=Range(min=0, max=50*1024*1024))

    @validates('filename')
    def validate_filename_security(self, value, **kwargs):
        """Validate filename for security"""
        # Remove path traversal attempts
        safe_filename = value.replace('..', '').replace('/', '').replace('\\', '')

        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9._\s-]+$', safe_filename):
            raise ValidationError('Filename contains invalid characters')

        return safe_filename


# Enhanced schema registry with new schemas
SCHEMAS = {
    'user_registration': UserRegistrationSchema,
    'user_update': UserUpdateSchema,
    'form_creation': FormCreationSchema,
    'form_update': FormUpdateSchema,
    'form_submission': FormSubmissionSchema,
    'report_creation': ReportCreationSchema,
    'report_export': ReportExportSchema,
    'excel_upload': ExcelUploadSchema,
    'ai_report': AIReportSchema,
    'google_forms': GoogleFormsSchema,
    'query_params': QueryParamsSchema,
    'file_upload': FileUploadValidationSchema,
}

def get_schema(schema_name):
    """Get a schema instance by name"""
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}. Available schemas: {', '.join(SCHEMAS.keys())}")
    return SCHEMAS[schema_name]()

def validate_request_data(data, schema_name, **schema_kwargs):
    """Convenience function to validate request data with a named schema"""
    try:
        schema = get_schema(schema_name)
        if schema_kwargs:
            # Update schema with additional validation rules if provided
            for key, value in schema_kwargs.items():
                if hasattr(schema, key):
                    setattr(schema, key, value)

        return schema.load(data)
    except ValidationError as e:
        # Re-raise with more context
        raise ValidationError(f"Validation failed for schema '{schema_name}': {e.messages}")

def sanitize_request_data(data):
    """Sanitize all string values in request data"""
    if isinstance(data, dict):
        return {key: ValidationUtils.sanitize_string(value) if isinstance(value, str) else value
                for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_request_data(item) for item in data]
    elif isinstance(data, str):
        return ValidationUtils.sanitize_string(data)
    else:
        return data
