"""
Validation decorators and utilities for Flask routes
Provides consistent validation patterns across all API endpoints
"""

from functools import wraps
from flask import request, jsonify, current_app
from marshmallow import ValidationError
from datetime import datetime
import logging


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
                
                # Get JSON data from request
                if not request.is_json:
                    return jsonify({
                        'error': True,
                        'message': 'Content-Type must be application/json',
                        'code': 'INVALID_CONTENT_TYPE'
                    }), 400
                
                json_data = request.get_json()
                if json_data is None:
                    return jsonify({
                        'error': True,
                        'message': 'Invalid JSON data',
                        'code': 'INVALID_JSON'
                    }), 400
                
                # Validate data
                validated_data = schema.load(json_data)
                
                # Call original function with validated data
                return f(validated_data, *args, **kwargs)
                
            except ValidationError as e:
                current_app.logger.warning(f"Validation error in {f.__name__}: {e.messages}")
                return jsonify({
                    'error': True,
                    'message': 'Validation failed',
                    'details': e.messages,
                    'code': 'VALIDATION_ERROR',
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
            except Exception as e:
                current_app.logger.error(f"Unexpected error in validation decorator: {str(e)}")
                return jsonify({
                    'error': True,
                    'message': 'Internal server error',
                    'code': 'INTERNAL_ERROR',
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
        
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
                return jsonify({
                    'error': True,
                    'message': 'Invalid query parameters',
                    'details': e.messages,
                    'code': 'INVALID_QUERY_PARAMS',
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
                
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
                    return jsonify({
                        'error': True,
                        'message': 'No files uploaded',
                        'code': 'NO_FILE_UPLOADED'
                    }), 400
                
                validated_files = {}
                for key, file in files.items():
                    if file.filename == '':
                        if required:
                            return jsonify({
                                'error': True,
                                'message': f'No file selected for {key}',
                                'code': 'NO_FILE_SELECTED'
                            }), 400
                        continue
                    
                    ValidationUtils.validate_file_upload(file, allowed_extensions, max_size_mb)
                    validated_files[key] = file
                
                return f(validated_files, *args, **kwargs)
                
            except ValidationError as e:
                return jsonify({
                    'error': True,
                    'message': str(e),
                    'code': 'FILE_VALIDATION_ERROR'
                }), 400
                
        return decorated_function
    return decorator


class ErrorHandler:
    """Centralized error handling for API responses"""
    
    @staticmethod
    def format_error_response(message, code=None, details=None, status_code=400):
        """Format standardized error response"""
        response = {
            'error': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if code:
            response['code'] = code
        
        if details:
            response['details'] = details
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors, message="Validation failed"):
        """Format validation error response"""
        return ErrorHandler.format_error_response(
            message=message,
            code='VALIDATION_ERROR',
            details=errors,
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
