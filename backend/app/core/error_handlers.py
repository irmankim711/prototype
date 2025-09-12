"""
Global Error Handlers for Flask Backend

This module provides global error handlers that catch various types of
exceptions and return standardized JSON error responses with appropriate
HTTP status codes.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from http import HTTPStatus

from flask import Flask, Request, Response, jsonify, current_app, request
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, Forbidden, NotFound
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError, OperationalError
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from .exceptions import (
    BaseAPIException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ConflictError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
    ConfigurationError,
    FileProcessingError,
    ReportGenerationError,
    AIAnalysisError
)

# Configure logging
logger = logging.getLogger(__name__)


class ErrorResponse:
    """
    Standardized error response format for all API errors.
    
    This class provides a consistent structure for error responses
    across the application, including error details, timestamps,
    and request tracking information.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.field_errors = field_errors or {}
        self.request_id = request_id
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary format."""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "timestamp": self.timestamp.isoformat(),
                "details": self.details
            },
            "success": False
        }
        
        if self.field_errors:
            response["error"]["field_errors"] = self.field_errors
        
        if self.request_id:
            response["error"]["request_id"] = self.request_id
        
        return response
    
    def to_response(self) -> Tuple[Response, int]:
        """Convert error response to Flask response tuple."""
        return jsonify(self.to_dict()), self.status_code


def create_error_response(
    error: Exception,
    request: Optional[Request] = None,
    include_details: bool = False
) -> ErrorResponse:
    """
    Create a standardized error response from an exception.
    
    Args:
        error: The exception that occurred
        request: The Flask request object (optional)
        include_details: Whether to include detailed error information
    
    Returns:
        ErrorResponse object with standardized format
    """
    request_id = None
    if request:
        request_id = request.headers.get('X-Request-ID')
    
    # Handle custom API exceptions
    if isinstance(error, BaseAPIException):
        details = error.details if include_details else {}
        return ErrorResponse(
            error_code=error.error_code,
            message=error.message,
            status_code=error.status_code,
            details=details,
            field_errors=getattr(error, 'field_errors', {}),
            request_id=request_id
        )
    
    # Handle validation errors
    if isinstance(error, MarshmallowValidationError):
        field_errors = {}
        if hasattr(error, 'messages'):
            field_errors = error.messages
        
        return ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            status_code=HTTPStatus.BAD_REQUEST,
            field_errors=field_errors,
            request_id=request_id
        )
    
    # Handle SQLAlchemy errors
    if isinstance(error, SQLAlchemyError):
        return handle_database_error(error, request_id, include_details)
    
    # Handle HTTP exceptions
    if isinstance(error, HTTPException):
        return ErrorResponse(
            error_code=f"HTTP_{error.code}",
            message=error.description or "HTTP error occurred",
            status_code=error.code,
            request_id=request_id
        )
    
    # Handle generic exceptions
    return ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        details={"exception_type": type(error).__name__} if include_details else {},
        request_id=request_id
    )


def handle_database_error(
    error: SQLAlchemyError,
    request_id: Optional[str],
    include_details: bool
) -> ErrorResponse:
    """Handle database-specific errors with user-friendly messages."""
    
    if isinstance(error, IntegrityError):
        # Handle constraint violations
        message = "Data integrity constraint violated"
        details = {}
        if include_details:
            details.update({
                "constraint": str(error.orig),
                "table": getattr(error, 'table', 'unknown')
            })
        
        return ErrorResponse(
            error_code="DATABASE_INTEGRITY_ERROR",
            message=message,
            status_code=HTTPStatus.CONFLICT,
            details=details,
            request_id=request_id
        )
    
    elif isinstance(error, DataError):
        # Handle data type errors
        message = "Invalid data format or type"
        details = {}
        if include_details:
            details.update({
                "data_error": str(error.orig),
                "statement": getattr(error, 'statement', 'unknown')
            })
        
        return ErrorResponse(
            error_code="DATABASE_DATA_ERROR",
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            details=details,
            request_id=request_id
        )
    
    elif isinstance(error, OperationalError):
        # Handle connection and operational errors
        message = "Database operation failed"
        details = {}
        if include_details:
            details.update({
                "operation_error": str(error.orig),
                "connection_info": getattr(error, 'connection_invalidated', False)
            })
        
        return ErrorResponse(
            error_code="DATABASE_OPERATIONAL_ERROR",
            message=message,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=details,
            request_id=request_id
        )
    
    else:
        # Generic database error
        message = "Database operation failed"
        details = {}
        if include_details:
            details.update({
                "sql_error": str(error),
                "exception_type": type(error).__name__
            })
        
        return ErrorResponse(
            error_code="DATABASE_ERROR",
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details,
            request_id=request_id
        )


def log_error(
    error: Exception,
    request: Optional[Request] = None,
    include_stack_trace: bool = True
) -> None:
    """
    Log error information with appropriate severity level.
    
    Args:
        error: The exception that occurred
        request: The Flask request object (optional)
        include_stack_trace: Whether to include full stack trace
    """
    # Determine log level based on error type
    if isinstance(error, (ValidationError, ResourceNotFoundError)):
        log_level = logging.WARNING
    elif isinstance(error, (AuthenticationError, AuthorizationError)):
        log_level = logging.INFO
    elif isinstance(error, (DatabaseError, ExternalServiceError)):
        log_level = logging.ERROR
    else:
        log_level = logging.ERROR
    
    # Prepare log message
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "status_code": getattr(error, 'status_code', 500)
    }
    
    if request:
        log_data.update({
            "method": request.method,
            "url": request.url,
            "user_agent": request.headers.get('User-Agent'),
            "ip_address": request.remote_addr,
            "request_id": request.headers.get('X-Request-ID')
        })
    
    # Log the error
    if log_level == logging.ERROR:
        logger.error("API Error: %s", log_data)
        if include_stack_trace:
            logger.error("Stack trace: %s", traceback.format_exc())
    elif log_level == logging.WARNING:
        logger.warning("API Warning: %s", log_data)
    else:
        logger.info("API Info: %s", log_data)


def send_to_sentry(error: Exception, request: Optional[Request] = None) -> None:
    """Send error to Sentry for error tracking."""
    try:
        if current_app.config.get('SENTRY_DSN'):
            with sentry_sdk.push_scope() as scope:
                if request:
                    scope.set_context("request", {
                        "method": request.method,
                        "url": request.url,
                        "headers": dict(request.headers),
                        "args": dict(request.args),
                        "form": dict(request.form)
                    })
                
                scope.set_tag("error_type", type(error).__name__)
                scope.set_tag("status_code", getattr(error, 'status_code', 500))
                
                sentry_sdk.capture_exception(error)
    except Exception as sentry_error:
        logger.warning("Failed to send error to Sentry: %s", sentry_error)


# Flask error handler functions
def handle_api_exception(error: BaseAPIException) -> Tuple[Response, int]:
    """Handle custom API exceptions."""
    request = current_app.request_context.top.request if current_app.request_context.top else None
    
    # Log the error
    log_error(error, request)
    
    # Send to Sentry if configured
    send_to_sentry(error, request)
    
    # Create and return error response
    error_response = create_error_response(error, request)
    return error_response.to_response()


def handle_validation_error(error: ValidationError) -> Tuple[Response, int]:
    """Handle validation errors."""
    request = current_app.request_context.top.request if current_app.request_context.top else None
    
    # Log the error
    log_error(error, request)
    
    # Create and return error response
    error_response = create_error_response(error, request)
    return error_response.to_response()


def handle_marshmallow_validation_error(error: MarshmallowValidationError) -> Tuple[Response, int]:
    """Handle Marshmallow validation errors."""
    request = current_app.request_context.top.request if current_app.request_context.top else None
    
    # Log the error
    log_error(error, request)
    
    # Create and return error response
    error_response = create_error_response(error, request)
    return error_response.to_response()


def handle_database_exception(error: SQLAlchemyError) -> Tuple[Response, int]:
    """Handle database exceptions."""
    request = current_app.request_context.top.request if current_app.request_context.top else None
    
    # Log the error
    log_error(error, request)
    
    # Send to Sentry if configured
    send_to_sentry(error, request)
    
    # Create and return error response
    error_response = create_error_response(error, request)
    return error_response.to_response()


def handle_http_exception(error: HTTPException) -> Tuple[Response, int]:
    """Handle HTTP exceptions."""
    try:
        request = request if 'request' in globals() else None
    except:
        request = None
    
    # Log the error
    log_error(error, request)
    
    # Create and return error response
    error_response = create_error_response(error, request)
    return error_response.to_response()


def handle_generic_exception(error: Exception) -> Tuple[Response, int]:
    """Handle generic exceptions."""
    try:
        request = request if 'request' in globals() else None
    except:
        request = None
    
    # Log the error
    log_error(error, request)
    
    # Send to Sentry if configured
    send_to_sentry(error, request)
    
    # Create and return error response
    error_response = create_error_response(error, request)
    return error_response.to_response()


def register_error_handlers(app: Flask) -> None:
    """
    Register all error handlers with the Flask application.
    
    Args:
        app: The Flask application instance
    """
    
    # Register custom exception handlers
    app.register_error_handler(BaseAPIException, handle_api_exception)
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(MarshmallowValidationError, handle_marshmallow_validation_error)
    app.register_error_handler(SQLAlchemyError, handle_database_exception)
    
    # Register HTTP exception handlers
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(BadRequest, handle_http_exception)
    app.register_error_handler(Unauthorized, handle_http_exception)
    app.register_error_handler(Forbidden, handle_http_exception)
    app.register_error_handler(NotFound, handle_http_exception)
    
    # Register generic exception handler (catches all unhandled exceptions)
    app.register_error_handler(Exception, handle_generic_exception)
    
    # Register 404 handler for undefined routes
    @app.errorhandler(404)
    def not_found_handler(error):
        """Handle 404 errors for undefined routes."""
        try:
            current_request = request if hasattr(request, 'url') else None
        except:
            current_request = None
        
        error_response = ErrorResponse(
            error_code="ENDPOINT_NOT_FOUND",
            message="The requested endpoint was not found",
            status_code=404,
            details={"requested_url": current_request.url if current_request else "unknown"},
            request_id=current_request.headers.get('X-Request-ID') if current_request else None
        )
        
        log_error(error, current_request)
        return error_response.to_response()
    
    # Register 405 handler for method not allowed
    @app.errorhandler(405)
    def method_not_allowed_handler(error):
        """Handle 405 errors for unsupported HTTP methods."""
        try:
            current_request = request if hasattr(request, 'method') else None
        except:
            current_request = None
        
        error_response = ErrorResponse(
            error_code="METHOD_NOT_ALLOWED",
            message="The HTTP method is not allowed for this endpoint",
            status_code=405,
            details={
                "method": current_request.method if current_request else "unknown",
                "allowed_methods": getattr(error, 'valid_methods', [])
            },
            request_id=current_request.headers.get('X-Request-ID') if current_request else None
        )
        
        log_error(error, current_request)
        return error_response.to_response()
    
    # Register 500 handler for internal server errors
    @app.errorhandler(500)
    def internal_server_error_handler(error):
        """Handle 500 internal server errors."""
        try:
            current_request = request if hasattr(request, 'headers') else None
        except:
            current_request = None
        
        error_response = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            status_code=500,
            request_id=current_request.headers.get('X-Request-ID') if current_request else None
        )
        
        log_error(error, current_request)
        send_to_sentry(error, current_request)
        return error_response.to_response()


def configure_sentry(app: Flask) -> None:
    """
    Configure Sentry integration for error tracking.
    
    Args:
        app: The Flask application instance
    """
    sentry_dsn = app.config.get('SENTRY_DSN')
    if sentry_dsn:
        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                environment=app.config.get('FLASK_ENV', 'development'),
                traces_sample_rate=app.config.get('SENTRY_TRACES_SAMPLE_RATE', 0.1),
                profiles_sample_rate=app.config.get('SENTRY_PROFILES_SAMPLE_RATE', 0.1),
                before_send=lambda event, hint: event
            )
            logger.info("Sentry integration configured successfully")
        except Exception as e:
            logger.warning("Failed to configure Sentry: %s", e)
    else:
        logger.info("Sentry DSN not configured, skipping Sentry integration")


def create_error_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Create error response schemas for API documentation.
    
    Returns:
        Dictionary containing error response schemas
    """
    return {
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Error code identifier"
                        },
                        "message": {
                            "type": "string",
                            "description": "Human-readable error message"
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "When the error occurred"
                        },
                        "details": {
                            "type": "object",
                            "description": "Additional error details"
                        },
                        "field_errors": {
                            "type": "object",
                            "description": "Field-specific validation errors"
                        },
                        "request_id": {
                            "type": "string",
                            "description": "Unique request identifier for tracking"
                        }
                    },
                    "required": ["code", "message", "timestamp"]
                },
                "success": {
                    "type": "boolean",
                    "description": "Always false for error responses"
                }
            },
            "required": ["error", "success"]
        },
        "ValidationError": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "example": "VALIDATION_ERROR"
                        },
                        "message": {
                            "type": "string",
                            "example": "Validation failed"
                        },
                        "field_errors": {
                            "type": "object",
                            "example": {
                                "email": ["Invalid email format"],
                                "password": ["Password must be at least 8 characters"]
                            }
                        }
                    }
                }
            }
        },
        "AuthenticationError": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "example": "AUTHENTICATION_ERROR"
                        },
                        "message": {
                            "type": "string",
                            "example": "Authentication failed"
                        }
                    }
                }
            }
        },
        "ResourceNotFoundError": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "example": "RESOURCE_NOT_FOUND"
                        },
                        "message": {
                            "type": "string",
                            "example": "User with ID '123' not found"
                        }
                    }
                }
            }
        }
    }
