"""
Validation decorators and utilities for Flask routes
Provides consistent validation patterns across all API endpoints
"""

from functools import wraps
from flask import request, jsonify, current_app, g
from marshmallow import ValidationError
from datetime import datetime
import logging
import uuid
import traceback


def validate_json(schema_class, **schema_kwargs):
    """
    Decorator to validate JSON request data using Marshmallow schema
    
    Args:
        schema_class: Marshmallow schema class to use for validation
        **schema_kwargs: Additional arguments to pass to schema constructor
    
    Usage:
        @validate_json(UserRegistrationSchema)
        def create_user(validated_data):
            # validated_data contains the validated and parsed data
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Initialize schema
                schema = schema_class(**schema_kwargs)
                
                # Ensure request ID is set
                if not hasattr(g, 'request_id'):
                    g.request_id = str(uuid.uuid4())

                # Get JSON data from request
                if not request.is_json:
                    return ErrorHandler.content_type_error()

                json_data = request.get_json()
                if json_data is None:
                    return ErrorHandler.format_error_response(
                        message='Invalid or empty JSON data',
                        code='INVALID_JSON',
                        details={
                            'suggestion': 'Ensure the request body contains valid JSON'
                        }
                    )
                
                # Validate data
                validated_data = schema.load(json_data)
                
                # Call original function with validated data
                return f(validated_data, *args, **kwargs)
                
            except ValidationError as e:
                current_app.logger.warning(f"Validation error in {f.__name__}: {e.messages}")
                return ErrorHandler.validation_error(
                    errors=e.messages,
                    message='Request validation failed'
                )
            except Exception as e:
                current_app.logger.error(f"Unexpected error in validation decorator: {str(e)}")
                current_app.logger.error(f"Traceback: {traceback.format_exc()}")
                return ErrorHandler.internal_error(
                    message='An unexpected error occurred during validation'
                )
        
        return decorated_function
    return decorator


def validate_query_params(schema_class, **schema_kwargs):
    """
    Decorator to validate query parameters using Marshmallow schema
    
    Usage:
        @validate_query_params(PaginationSchema)
        def get_items(validated_params):
            page = validated_params['page']
            per_page = validated_params['per_page']
            # ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class(**schema_kwargs)
                
                # Convert query args to dict
                query_data = request.args.to_dict()
                
                # Handle multi-value parameters
                for key in request.args.keys():
                    values = request.args.getlist(key)
                    if len(values) > 1:
                        query_data[key] = values
                
                validated_data = schema.load(query_data)
                return f(validated_data, *args, **kwargs)
                
            except ValidationError as e:
                return ErrorHandler.validation_error(
                    errors=e.messages,
                    message='Invalid query parameters'
                )
                
        return decorated_function
    return decorator


def validate_file_upload(allowed_extensions=None, max_size_mb=10, required=True):
    """
    Decorator to validate file uploads
    
    Args:
        allowed_extensions: List of allowed file extensions
        max_size_mb: Maximum file size in MB
        required: Whether file is required
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from .schemas import ValidationUtils
                
                files = request.files
                if required and not files:
                    return ErrorHandler.file_upload_error(
                        message='No files uploaded',
                        allowed_types=allowed_extensions
                    )
                
                validated_files = {}
                for key, file in files.items():
                    if file.filename == '':
                        if required:
                            return ErrorHandler.file_upload_error(
                                message=f'No file selected for field: {key}',
                                allowed_types=allowed_extensions
                            )
                        continue
                    
                    ValidationUtils.validate_file_upload(file, allowed_extensions, max_size_mb)
                    validated_files[key] = file
                
                return f(validated_files, *args, **kwargs)
                
            except ValidationError as e:
                return ErrorHandler.file_upload_error(
                    message=str(e),
                    allowed_types=allowed_extensions,
                    max_size_mb=max_size_mb
                )
                
        return decorated_function
    return decorator


class ErrorHandler:
    """Centralized error handling for API responses"""

    @staticmethod
    def format_error_response(message, code=None, details=None, status_code=400, request_id=None):
        """Format standardized error response with enhanced context"""
        if not request_id:
            request_id = getattr(g, 'request_id', None) or str(uuid.uuid4())

        response = {
            'success': False,
            'error': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request_id,
            'status_code': status_code
        }

        if code:
            response['code'] = code

        if details:
            response['details'] = details

        # Add request context for debugging
        if current_app.debug:
            response['debug_info'] = {
                'endpoint': request.endpoint,
                'method': request.method,
                'url': request.url,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }

        # Log the error for monitoring
        current_app.logger.error(
            f"API Error {status_code}: {message} | "
            f"Request ID: {request_id} | "
            f"Endpoint: {request.endpoint} | "
            f"Method: {request.method}"
        )

        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors, message="Validation failed", field_suggestions=None):
        """Format validation error response with field suggestions"""
        details = {
            'field_errors': errors if isinstance(errors, dict) else {'general': errors},
            'total_errors': len(errors) if isinstance(errors, dict) else 1
        }

        if field_suggestions:
            details['suggestions'] = field_suggestions

        return ErrorHandler.format_error_response(
            message=message,
            code='VALIDATION_ERROR',
            details=details,
            status_code=400
        )
    
    @staticmethod
    def not_found_error(resource="Resource"):
        """Format not found error response"""
        return ErrorHandler.format_error_response(
            message=f"{resource} not found",
            code='NOT_FOUND',
            status_code=404
        )
    
    @staticmethod
    def unauthorized_error(message="Unauthorized access"):
        """Format unauthorized error response"""
        return ErrorHandler.format_error_response(
            message=message,
            code='UNAUTHORIZED',
            status_code=401
        )
    
    @staticmethod
    def forbidden_error(message="Access forbidden"):
        """Format forbidden error response"""
        return ErrorHandler.format_error_response(
            message=message,
            code='FORBIDDEN',
            status_code=403
        )
    
    @staticmethod
    def internal_error(message="Internal server error"):
        """Format internal server error response"""
        return ErrorHandler.format_error_response(
            message=message,
            code='INTERNAL_ERROR',
            status_code=500
        )

    @staticmethod
    def bad_request_error(message="Bad request", missing_fields=None, invalid_fields=None):
        """Format bad request error with specific field information"""
        details = {}

        if missing_fields:
            details['missing_fields'] = missing_fields
            details['suggestion'] = f"Please provide the following required fields: {', '.join(missing_fields)}"

        if invalid_fields:
            details['invalid_fields'] = invalid_fields
            details['suggestion'] = f"Please check the format of: {', '.join(invalid_fields.keys())}"

        return ErrorHandler.format_error_response(
            message=message,
            code='BAD_REQUEST',
            details=details,
            status_code=400
        )

    @staticmethod
    def file_upload_error(message="File upload error", allowed_types=None, max_size_mb=None):
        """Format file upload error response"""
        details = {}

        if allowed_types:
            details['allowed_file_types'] = allowed_types
            details['suggestion'] = f"Please upload a file with one of these extensions: {', '.join(allowed_types)}"

        if max_size_mb:
            details['max_file_size_mb'] = max_size_mb
            details['suggestion'] = f"File size must be less than {max_size_mb}MB"

        return ErrorHandler.format_error_response(
            message=message,
            code='FILE_UPLOAD_ERROR',
            details=details,
            status_code=400
        )

    @staticmethod
    def content_type_error(expected_type="application/json"):
        """Format content type error response"""
        return ErrorHandler.format_error_response(
            message=f"Invalid Content-Type. Expected: {expected_type}",
            code='INVALID_CONTENT_TYPE',
            details={
                'expected_content_type': expected_type,
                'received_content_type': request.headers.get('Content-Type', 'Not specified'),
                'suggestion': f"Set the Content-Type header to {expected_type}"
            },
            status_code=400
        )


class RequestValidator:
    """Utility class for common request validations"""
    
    @staticmethod
    def validate_pagination(page=None, per_page=None, max_per_page=100):
        """Validate and return pagination parameters"""
        try:
            page = int(page) if page else 1
            per_page = int(per_page) if per_page else 20
        except (ValueError, TypeError):
            raise ValidationError('Page and per_page must be valid integers')
        
        if page < 1:
            raise ValidationError('Page must be greater than 0')
        
        if per_page < 1 or per_page > max_per_page:
            raise ValidationError(f'Per page must be between 1 and {max_per_page}')
        
        return page, per_page
    
    @staticmethod
    def validate_sort_params(sort_by=None, sort_order='asc', allowed_fields=None):
        """Validate sorting parameters"""
        if sort_order not in ['asc', 'desc']:
            raise ValidationError('Sort order must be "asc" or "desc"')
        
        if sort_by and allowed_fields and sort_by not in allowed_fields:
            raise ValidationError(f'Sort field must be one of: {", ".join(allowed_fields)}')
        
        return sort_by, sort_order
    
    @staticmethod
    def validate_date_range(start_date=None, end_date=None):
        """Validate date range parameters"""
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError('Start date must be in ISO format')
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError('End date must be in ISO format')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError('Start date must be before end date')
        
        return start_date, end_date


def handle_validation_errors(f):
    """Decorator to catch and handle validation errors consistently"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return ErrorHandler.validation_error(e.messages)
        except Exception as e:
            current_app.logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return ErrorHandler.internal_error()
    
    return decorated_function


# Middleware for request logging and validation
def log_request_validation(f):
    """Decorator to log request validation details"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.utcnow()
        
        # Log request details
        current_app.logger.info(f"Validating request to {request.endpoint}")
        current_app.logger.debug(f"Request method: {request.method}")
        current_app.logger.debug(f"Request args: {request.args.to_dict()}")
        
        if request.is_json:
            current_app.logger.debug(f"Request JSON keys: {list(request.get_json().keys()) if request.get_json() else 'None'}")
        
        try:
            result = f(*args, **kwargs)
            
            # Log successful validation
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            current_app.logger.info(f"Request validation completed in {duration:.3f}s")
            
            return result
            
        except Exception as e:
            # Log validation failure
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            current_app.logger.warning(f"Request validation failed in {duration:.3f}s: {str(e)}")
            raise
    
    return decorated_function
