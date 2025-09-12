"""
Custom Exception Classes for Flask Backend

This module defines custom exception classes for different types of errors
that can occur in the application, providing a structured way to handle
and respond to various error scenarios.
"""

from typing import Any, Dict, List, Optional, Union
from http import HTTPStatus


class BaseAPIException(Exception):
    """
    Base exception class for all API-related errors.
    
    This class provides a foundation for all custom exceptions and includes
    common attributes like status code, error code, and message.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.headers = headers or {}


class ValidationError(BaseAPIException):
    """
    Exception raised when request validation fails.
    
    This exception is used for input validation errors, including
    field-specific errors and validation rule violations.
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )
        self.field_errors = field_errors or {}


class AuthenticationError(BaseAPIException):
    """
    Exception raised when authentication fails.
    
    This exception is used for login failures, invalid credentials,
    and other authentication-related issues.
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details or {}
        )


class AuthorizationError(BaseAPIException):
    """
    Exception raised when authorization fails.
    
    This exception is used when a user is authenticated but doesn't
    have permission to access a resource or perform an action.
    """
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permissions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details or {}
        )
        self.required_permissions = required_permissions or []


class ResourceNotFoundError(BaseAPIException):
    """
    Exception raised when a requested resource is not found.
    
    This exception is used for 404 errors when trying to access
    resources that don't exist.
    """
    
    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: Optional[Union[str, int]] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            if resource_id is not None:
                message = f"{resource_type} with ID '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"
        
        super().__init__(
            message=message,
            status_code=HTTPStatus.NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details=details or {}
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictError(BaseAPIException):
    """
    Exception raised when there's a conflict with existing data.
    
    This exception is used for 409 conflicts, such as duplicate
    entries or business rule violations.
    """
    
    def __init__(
        self,
        message: str = "Resource conflict",
        conflict_field: Optional[str] = None,
        existing_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.CONFLICT,
            error_code="CONFLICT_ERROR",
            details=details or {}
        )
        self.conflict_field = conflict_field
        self.existing_value = existing_value


class RateLimitError(BaseAPIException):
    """
    Exception raised when rate limiting is exceeded.
    
    This exception is used for 429 rate limit exceeded errors,
    providing information about retry timing.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR",
            details=details or {}
        )
        self.retry_after = retry_after
        self.limit = limit
        self.window = window


class DatabaseError(BaseAPIException):
    """
    Exception raised when database operations fail.
    
    This exception is used for database-related errors, providing
    user-friendly messages while logging technical details.
    """
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table: Optional[str] = None,
        constraint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details or {}
        )
        self.operation = operation
        self.table = table
        self.constraint = constraint


class ExternalServiceError(BaseAPIException):
    """
    Exception raised when external service calls fail.
    
    This exception is used for errors from third-party services,
    APIs, or external integrations.
    """
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        service_url: Optional[str] = None,
        response_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details or {}
        )
        self.service_name = service_name
        self.service_url = service_url
        self.response_status = response_status


class ConfigurationError(BaseAPIException):
    """
    Exception raised when there's a configuration issue.
    
    This exception is used for missing or invalid configuration
    values that prevent the application from running properly.
    """
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR",
            details=details or {}
        )
        self.config_key = config_key
        self.expected_type = expected_type


class FileProcessingError(BaseAPIException):
    """
    Exception raised when file processing operations fail.
    
    This exception is used for file upload, processing, or
    manipulation errors.
    """
    
    def __init__(
        self,
        message: str = "File processing failed",
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            error_code="FILE_PROCESSING_ERROR",
            details=details or {}
        )
        self.file_name = file_name
        self.file_size = file_size
        self.operation = operation


class ReportGenerationError(BaseAPIException):
    """
    Exception raised when report generation fails.
    
    This exception is used for errors during report creation,
    template processing, or document generation.
    """
    
    def __init__(
        self,
        message: str = "Report generation failed",
        template_name: Optional[str] = None,
        report_type: Optional[str] = None,
        generation_step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="REPORT_GENERATION_ERROR",
            details=details or {}
        )
        self.template_name = template_name
        self.report_type = report_type
        self.generation_step = generation_step


class AIAnalysisError(BaseAPIException):
    """
    Exception raised when AI analysis operations fail.
    
    This exception is used for errors during AI processing,
    model inference, or analysis operations.
    """
    
    def __init__(
        self,
        message: str = "AI analysis failed",
        model_name: Optional[str] = None,
        analysis_type: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="AI_ANALYSIS_ERROR",
            details=details or {}
        )
        self.model_name = model_name
        self.analysis_type = analysis_type
        self.input_data = input_data


# Convenience functions for common error scenarios
def validation_error(
    field_errors: Dict[str, List[str]],
    message: str = "Validation failed"
) -> ValidationError:
    """Create a validation error with field-specific errors."""
    return ValidationError(message=message, field_errors=field_errors)


def not_found_error(
    resource_type: str,
    resource_id: Optional[Union[str, int]] = None
) -> ResourceNotFoundError:
    """Create a resource not found error."""
    return ResourceNotFoundError(resource_type=resource_type, resource_id=resource_id)


def conflict_error(
    message: str,
    conflict_field: Optional[str] = None,
    existing_value: Optional[Any] = None
) -> ConflictError:
    """Create a conflict error."""
    return ConflictError(
        message=message,
        conflict_field=conflict_field,
        existing_value=existing_value
    )


def database_error(
    message: str,
    operation: Optional[str] = None,
    table: Optional[str] = None
) -> DatabaseError:
    """Create a database error."""
    return DatabaseError(
        message=message,
        operation=operation,
        table=table
    )


def external_service_error(
    message: str,
    service_name: str,
    service_url: Optional[str] = None
) -> ExternalServiceError:
    """Create an external service error."""
    return ExternalServiceError(
        message=message,
        service_name=service_name,
        service_url=service_url
    )
