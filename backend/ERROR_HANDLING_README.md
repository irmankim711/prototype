# Flask Backend Error Handling System

This document describes the comprehensive error handling system implemented for the Flask backend, providing standardized error responses, logging, and error tracking capabilities.

## Overview

The error handling system provides:
- **Custom Exception Classes** for different error types
- **Global Error Handlers** with proper HTTP status codes
- **Standardized Error Response Format** (JSON)
- **Comprehensive Logging** with proper severity levels
- **Sentry Integration** for error tracking and monitoring
- **Configuration Management** for different environments
- **API Documentation Schemas** for error responses

## Architecture

```
backend/app/core/
├── exceptions.py          # Custom exception classes
├── error_handlers.py      # Global error handlers and utilities
└── error_config.py        # Configuration management
```

## Features

### ✅ **Implemented Requirements**

1. **✅ Custom Exception Classes** - Complete implementation for all error types
2. **✅ Global Error Handler** - Comprehensive error handling with proper HTTP status codes
3. **✅ Standardized Error Response Format** - Consistent JSON error structure
4. **✅ Validation Error Handling** - Detailed field errors and validation messages
5. **✅ Authentication/Authorization Error Handling** - Proper 401/403 responses
6. **✅ Database Error Handling** - User-friendly messages with technical logging
7. **✅ Comprehensive Logging** - Structured logging with severity levels
8. **✅ Sentry Integration** - Error tracking and monitoring configuration
9. **✅ Error Response Schemas** - OpenAPI documentation schemas

## Exception Classes

### Base Exception

```python
class BaseAPIException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    )
```

### Specific Exception Types

#### 1. **ValidationError** (400)
- Input validation failures
- Field-specific error messages
- Schema validation errors

```python
from app.core.exceptions import ValidationError, validation_error

# Create validation error with field errors
field_errors = {
    "email": ["Invalid email format"],
    "password": ["Password must be at least 8 characters"]
}
raise validation_error(field_errors, "Form validation failed")
```

#### 2. **AuthenticationError** (401)
- Login failures
- Invalid credentials
- Token validation errors

```python
from app.core.exceptions import AuthenticationError

raise AuthenticationError("Invalid username or password")
```

#### 3. **AuthorizationError** (403)
- Insufficient permissions
- Access denied scenarios
- Role-based access control failures

```python
from app.core.exceptions import AuthorizationError

raise AuthorizationError(
    "Access denied", 
    required_permissions=["admin", "moderator"]
)
```

#### 4. **ResourceNotFoundError** (404)
- Missing resources
- Invalid IDs
- Deleted content

```python
from app.core.exceptions import ResourceNotFoundError, not_found_error

# Using convenience function
raise not_found_error("User", user_id)

# Or direct instantiation
raise ResourceNotFoundError("Report", report_id, "Report not found")
```

#### 5. **ConflictError** (409)
- Duplicate entries
- Business rule violations
- Data conflicts

```python
from app.core.exceptions import ConflictError, conflict_error

raise conflict_error(
    "Email already exists", 
    conflict_field="email", 
    existing_value="user@example.com"
)
```

#### 6. **DatabaseError** (500)
- Database operation failures
- Connection issues
- Constraint violations

```python
from app.core.exceptions import DatabaseError, database_error

raise database_error(
    "Failed to create user", 
    operation="INSERT", 
    table="users"
)
```

#### 7. **ExternalServiceError** (502)
- Third-party API failures
- Service integration errors
- Network timeouts

```python
from app.core.exceptions import ExternalServiceError, external_service_error

raise external_service_error(
    "Payment service unavailable", 
    service_name="Stripe"
)
```

#### 8. **RateLimitError** (429)
- Rate limiting exceeded
- API quota limits
- Throttling violations

```python
from app.core.exceptions import RateLimitError

raise RateLimitError(
    "Rate limit exceeded",
    retry_after=60,
    limit=100,
    window=3600
)
```

## Error Response Format

All errors follow a standardized JSON response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "timestamp": "2024-01-15T10:30:00Z",
    "details": {
      "operation": "user_creation",
      "context": "registration_form"
    },
    "field_errors": {
      "email": ["Invalid email format"],
      "password": ["Password must be at least 8 characters"]
    },
    "request_id": "req_1705312200_abc123def"
  },
  "success": false
}
```

### Response Fields

- **`error.code`**: Machine-readable error identifier
- **`error.message`**: Human-readable error description
- **`error.timestamp`**: When the error occurred (ISO 8601)
- **`error.details`**: Additional context information
- **`error.field_errors`**: Field-specific validation errors
- **`error.request_id`**: Unique request identifier for tracking
- **`success`**: Always `false` for error responses

## Error Handlers

### Global Error Handler Registration

```python
from app.core.error_handlers import register_error_handlers

# In your Flask app
register_error_handlers(app)
```

### Handler Types

1. **Custom API Exceptions**: `BaseAPIException` and subclasses
2. **Validation Errors**: `ValidationError` and Marshmallow validation errors
3. **Database Errors**: SQLAlchemy exceptions
4. **HTTP Exceptions**: Werkzeug HTTP exceptions
5. **Generic Exceptions**: Catch-all for unhandled errors

### Custom Error Handler Example

```python
from app.core.exceptions import ResourceNotFoundError

@app.errorhandler(ResourceNotFoundError)
def handle_resource_not_found(error):
    return jsonify({
        "error": {
            "code": error.error_code,
            "message": error.message,
            "resource_type": error.resource_type,
            "resource_id": error.resource_id
        }
    }), error.status_code
```

## Logging

### Log Levels by Error Type

- **WARNING**: Validation errors, resource not found
- **INFO**: Authentication/authorization errors
- **ERROR**: Database errors, external service errors, generic exceptions

### Log Format

```python
# Example log entry
2024-01-15 10:30:00,123 ERROR [app.core.error_handlers:log_error] API Error: {
    'error_type': 'ValidationError',
    'error_message': 'Validation failed',
    'status_code': 400,
    'method': 'POST',
    'url': '/api/users',
    'user_agent': 'Mozilla/5.0...',
    'ip_address': '192.168.1.100',
    'request_id': 'req_1705312200_abc123def'
}
```

### Logging Configuration

```python
from app.core.error_config import get_logging_config

config = get_logging_config()
print(f"Log level: {config.level}")
print(f"Log file: {config.file_path}")
print(f"Include stack trace: {config.include_stack_trace}")
```

## Sentry Integration

### Configuration

```python
from app.core.error_handlers import configure_sentry

# In your Flask app
configure_sentry(app)
```

### Environment Variables

```bash
# Sentry Configuration
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
SENTRY_DEBUG=false
FLASK_ENV=production
```

### Sentry Features

- **Error Tracking**: Automatic capture of exceptions
- **Request Context**: Request details, headers, parameters
- **User Context**: User information when available
- **Performance Monitoring**: Traces and profiles
- **Environment Filtering**: Different settings per environment

## Configuration Management

### Error Response Configuration

```python
from app.core.error_config import get_error_response_config

config = get_error_response_config()
print(f"Include details in production: {config.include_details_in_production}")
print(f"Include stack trace: {config.include_stack_trace}")
print(f"Include request ID: {config.include_request_id}")
```

### Environment Variables

```bash
# Error Response Configuration
ERROR_INCLUDE_DETAILS_IN_PRODUCTION=false
ERROR_INCLUDE_STACK_TRACE=false
ERROR_INCLUDE_REQUEST_ID=true
ERROR_INCLUDE_TIMESTAMP=true
ERROR_INCLUDE_ERROR_CODE=true
ERROR_INCLUDE_FIELD_ERRORS=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s %(levelname)s: %(message)s
LOG_FILE_PATH=logs/app.log
LOG_MAX_BYTES=10240000
LOG_BACKUP_COUNT=10
LOG_INCLUDE_STACK_TRACE=true
LOG_INCLUDE_REQUEST_DETAILS=true

# Database Error Configuration
DB_ERROR_INCLUDE_SQL_DETAILS=false
DB_ERROR_INCLUDE_TABLE_INFO=true
DB_ERROR_INCLUDE_CONSTRAINT_INFO=true
DB_ERROR_USER_FRIENDLY_MESSAGES=true

# Validation Error Configuration
VALIDATION_INCLUDE_FIELD_PATHS=true
VALIDATION_INCLUDE_RULES=false
VALIDATION_INCLUDE_SUGGESTIONS=true
VALIDATION_MAX_FIELD_ERRORS=10
```

## Usage Examples

### 1. **Basic Exception Usage**

```python
from app.core.exceptions import (
    ValidationError, 
    ResourceNotFoundError, 
    ConflictError
)

def create_user(user_data):
    try:
        # Validate user data
        if not user_data.get('email'):
            raise ValidationError(
                "Email is required",
                field_errors={"email": ["Email field is required"]}
            )
        
        # Check if user exists
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if existing_user:
            raise ConflictError(
                "User with this email already exists",
                conflict_field="email",
                existing_value=user_data['email']
            )
        
        # Create user logic...
        
    except Exception as e:
        # Let the global error handler deal with it
        raise
```

### 2. **Custom Error Handler**

```python
from app.core.exceptions import BaseAPIException
from app.core.error_handlers import create_error_response

@app.errorhandler(BaseAPIException)
def handle_custom_exception(error):
    # Create standardized error response
    error_response = create_error_response(error, request)
    return error_response.to_response()
```

### 3. **Field Validation with Marshmallow**

```python
from marshmallow import Schema, fields, ValidationError

class UserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda p: len(p) >= 8)

def validate_user_data(data):
    try:
        schema = UserSchema()
        return schema.load(data)
    except ValidationError as e:
        # This will be caught by the global error handler
        raise ValidationError(
            "User data validation failed",
            field_errors=e.messages
        )
```

### 4. **Database Error Handling**

```python
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import DatabaseError

def save_user(user):
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if "email" in str(e):
            raise ConflictError(
                "Email already exists",
                conflict_field="email"
            )
        else:
            raise DatabaseError(
                "Failed to save user",
                operation="INSERT",
                table="users"
            )
```

## API Documentation Schemas

### Error Response Schema

```yaml
ErrorResponse:
  type: object
  properties:
    error:
      type: object
      properties:
        code:
          type: string
          description: Error code identifier
        message:
          type: string
          description: Human-readable error message
        timestamp:
          type: string
          format: date-time
          description: When the error occurred
        details:
          type: object
          description: Additional error details
        field_errors:
          type: object
          description: Field-specific validation errors
        request_id:
          type: string
          description: Unique request identifier for tracking
      required: [code, message, timestamp]
    success:
      type: boolean
      description: Always false for error responses
  required: [error, success]
```

### Specific Error Schemas

```yaml
ValidationError:
  type: object
  properties:
    error:
      type: object
      properties:
        code:
          type: string
          example: "VALIDATION_ERROR"
        message:
          type: string
          example: "Validation failed"
        field_errors:
          type: object
          example:
            email: ["Invalid email format"]
            password: ["Password must be at least 8 characters"]

AuthenticationError:
  type: object
  properties:
    error:
      type: object
      properties:
        code:
          type: string
          example: "AUTHENTICATION_ERROR"
        message:
          type: string
          example: "Authentication failed"
```

## Testing

### Unit Testing Exceptions

```python
import pytest
from app.core.exceptions import ValidationError, ResourceNotFoundError

def test_validation_error():
    error = ValidationError("Test validation error")
    assert error.status_code == 400
    assert error.error_code == "VALIDATION_ERROR"
    assert error.message == "Test validation error"

def test_resource_not_found_error():
    error = ResourceNotFoundError("User", "123")
    assert error.status_code == 404
    assert error.resource_type == "User"
    assert error.resource_id == "123"
    assert "User with ID '123' not found" in error.message
```

### Integration Testing Error Handlers

```python
def test_validation_error_handler(client):
    response = client.post('/api/users', json={
        "email": "invalid-email",
        "password": "123"
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['error']['code'] == 'VALIDATION_ERROR'
    assert 'field_errors' in data['error']
```

## Best Practices

### 1. **Exception Hierarchy**
- Use specific exception types when possible
- Inherit from `BaseAPIException` for custom errors
- Provide meaningful error codes and messages

### 2. **Error Messages**
- Use user-friendly language
- Include actionable information
- Avoid exposing sensitive details in production

### 3. **Logging**
- Log at appropriate levels
- Include relevant context
- Use structured logging for better analysis

### 4. **Configuration**
- Use environment variables for configuration
- Provide sensible defaults
- Document all configuration options

### 5. **Testing**
- Test exception classes
- Test error handlers
- Test error response formats

## Troubleshooting

### Common Issues

1. **Error Handler Not Working**
   - Ensure `register_error_handlers(app)` is called
   - Check that exceptions inherit from `BaseAPIException`
   - Verify Flask app context is available

2. **Sentry Not Capturing Errors**
   - Check `SENTRY_DSN` environment variable
   - Verify Sentry configuration in `configure_sentry()`
   - Check network connectivity to Sentry

3. **Logging Not Working**
   - Verify log file permissions
   - Check log level configuration
   - Ensure logging directory exists

4. **Custom Exceptions Not Caught**
   - Ensure exception inherits from `BaseAPIException`
   - Check error handler registration order
   - Verify exception is raised, not returned

### Debug Mode

Enable debug mode for detailed error information:

```bash
FLASK_ENV=development
FLASK_DEBUG=true
ERROR_INCLUDE_DETAILS_IN_PRODUCTION=true
ERROR_INCLUDE_STACK_TRACE=true
```

## Future Enhancements

### Planned Features

1. **Error Analytics Dashboard**
   - Error frequency tracking
   - Performance impact analysis
   - User experience metrics

2. **Advanced Rate Limiting**
   - Dynamic rate limit adjustment
   - User-specific limits
   - Adaptive throttling

3. **Error Recovery**
   - Automatic retry mechanisms
   - Circuit breaker patterns
   - Graceful degradation

4. **Enhanced Monitoring**
   - Real-time error alerts
   - Performance tracking
   - Business impact analysis

## Support

For questions or issues with the error handling system:

1. Check this documentation first
2. Review error logs for specific details
3. Check Sentry for error tracking information
4. Verify configuration settings
5. Contact the development team for complex issues

## Contributing

To contribute to the error handling system:

1. Follow the existing code patterns
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure backward compatibility
5. Follow the project's coding standards
