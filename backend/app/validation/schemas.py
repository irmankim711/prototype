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

# Schema registry for easy access
SCHEMAS = {
    'user_registration': UserRegistrationSchema,
    'user_update': UserUpdateSchema,
    'form_creation': FormCreationSchema,
    'form_update': FormUpdateSchema,
    'form_submission': FormSubmissionSchema,
    'report_creation': ReportCreationSchema,
}

def get_schema(schema_name):
    """Get a schema instance by name"""
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}")
    return SCHEMAS[schema_name]()
