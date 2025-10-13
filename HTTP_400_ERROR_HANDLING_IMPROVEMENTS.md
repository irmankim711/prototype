# HTTP 400 Error Handling Improvements

## Overview

This document outlines the comprehensive improvements made to HTTP 400 (Bad Request) error handling across the application. The changes provide consistent, user-friendly error responses with detailed debugging information and enhanced security.

## 🎯 Key Improvements

### 1. Standardized Error Response Format

All API endpoints now return consistent error responses with the following structure:

```json
{
  "success": false,
  "error": true,
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field_errors": {},
    "suggestions": "Helpful suggestion",
    "missing_fields": [],
    "invalid_fields": {}
  },
  "timestamp": "2025-01-XX T XX:XX:XX.XXXXXX",
  "request_id": "uuid-v4-request-id",
  "status_code": 400
}
```

### 2. Enhanced Validation Decorators

**File**: `backend/app/validation/decorators.py`

- **Request ID Tracking**: Every request gets a unique UUID for debugging
- **Enhanced Error Logging**: Detailed error context with request information
- **Standardized Error Types**: Specific error handlers for different scenarios:
  - `bad_request_error()` - Missing/invalid fields
  - `file_upload_error()` - File validation issues
  - `content_type_error()` - Invalid Content-Type headers
  - `validation_error()` - Schema validation failures

### 3. Comprehensive Validation Schemas

**File**: `backend/app/validation/schemas.py`

New validation schemas added:
- `ReportExportSchema` - Report export validation
- `ExcelUploadSchema` - Excel file upload validation
- `AIReportSchema` - AI report generation validation
- `GoogleFormsSchema` - Google Forms integration validation
- `QueryParamsSchema` - Common query parameter validation
- `FileUploadValidationSchema` - File metadata validation

### 4. Enhanced Security Features

**XSS Protection**:
```python
# Sanitizes dangerous content automatically
ValidationUtils.sanitize_string(user_input)
```

**File Upload Security**:
- Path traversal detection
- Filename validation
- Content type verification
- File size limits

### 5. Request Tracking Middleware

**File**: `backend/app/middleware/request_tracking.py`

- Generates unique request IDs for all requests
- Logs request start/completion with performance metrics
- Adds request ID to response headers for debugging

### 6. Frontend Error Handling Improvements

**File**: `frontend/src/services/enhancedApiService.ts`

Enhanced error categorization:
- `validation` - Schema validation errors
- `file_upload` - File upload specific errors
- `content_type` - Content-Type mismatch errors
- `auth` - Authentication/authorization errors
- `network` - Network connectivity issues

**Specific 400 Error Messages**:
```typescript
// Provides context-aware error messages
if (data?.code === 'VALIDATION_ERROR') {
  return `Validation failed (${errorCount} errors). Please check your input.`;
}

if (data?.code === 'FILE_UPLOAD_ERROR') {
  return `File upload error. Allowed types: ${allowedTypes.join(', ')}.`;
}
```

## 🔧 Implementation Details

### Backend Changes

1. **Error Handler Enhancement**:
   ```python
   # Before
   return jsonify({'error': 'Bad request'}), 400

   # After
   return ErrorHandler.bad_request_error(
       message='Request validation failed',
       missing_fields=['template_id'],
       invalid_fields={'formats': 'Must be an array'}
   )
   ```

2. **Validation Decorator Updates**:
   ```python
   # Enhanced JSON validation
   if not request.is_json:
       return ErrorHandler.content_type_error()

   if json_data is None:
       return ErrorHandler.format_error_response(
           message='Invalid or empty JSON data',
           code='INVALID_JSON'
       )
   ```

3. **File Upload Validation**:
   ```python
   # Security-focused file validation
   ValidationUtils.validate_file_upload(
       file,
       allowed_extensions=['.xlsx', '.xls', '.csv'],
       max_size_mb=50
   )
   ```

### Frontend Changes

1. **Enhanced Error Categorization**:
   ```typescript
   private getErrorType(error: AxiosError): ErrorType {
     const data = error.response?.data as any;

     if (data?.code === 'FILE_UPLOAD_ERROR') {
       return 'file_upload';
     }
     if (data?.code === 'VALIDATION_ERROR') {
       return 'validation';
     }
     // ... more specific categorization
   }
   ```

2. **Detailed Error Messages**:
   ```typescript
   // Context-aware user messages
   if (data?.code === 'BAD_REQUEST') {
     const missingFields = data?.details?.missing_fields;
     if (missingFields?.length > 0) {
       return `Missing required fields: ${missingFields.join(', ')}.`;
     }
   }
   ```

## 🚀 Usage Examples

### API Endpoint Implementation

```python
@reports_export_bp.route('/', methods=['POST'])
def export_reports():
    try:
        data = request.get_json(silent=True) or {}

        # Validate required fields
        missing_fields = []
        if not data.get('template_id'):
            missing_fields.append('template_id')
        if not data.get('data_source'):
            missing_fields.append('data_source')

        if missing_fields:
            return ErrorHandler.bad_request_error(
                message='Missing required fields for report export',
                missing_fields=missing_fields
            )

        # Continue with business logic...

    except Exception as e:
        return ErrorHandler.internal_error('Failed to export report')
```

### Frontend Error Handling

```typescript
try {
  const result = await enhancedApiService.post('/api/reports/export', data);
  return result;
} catch (error) {
  const errorInfo = enhancedApiService.getDetailedErrorInfo(error);

  if (errorInfo.errorCode === 'VALIDATION_ERROR') {
    // Show specific field errors
    displayFieldErrors(errorInfo.fieldErrors);
  } else if (errorInfo.errorCode === 'FILE_UPLOAD_ERROR') {
    // Show file upload specific guidance
    showFileUploadHelp(errorInfo.suggestions);
  }

  throw error;
}
```

## 🧪 Testing

**Test File**: `backend/test_400_error_handling.py`

Comprehensive test suite covering:
- Error response format consistency
- Validation error structures
- XSS protection
- File upload validation
- Request ID tracking
- API endpoint integration

Run tests:
```bash
cd backend
python test_400_error_handling.py
```

## 📊 Benefits

### For Developers
- **Consistent Debugging**: All errors include request IDs and context
- **Clear Error Categories**: Easy to understand what went wrong
- **Enhanced Logging**: Detailed error tracking for production issues

### For Users
- **Clear Error Messages**: User-friendly explanations instead of technical jargon
- **Actionable Feedback**: Specific guidance on how to fix issues
- **Better UX**: Reduced confusion with contextual error information

### For Security
- **XSS Protection**: Automatic sanitization of user inputs
- **File Upload Security**: Comprehensive validation and path traversal protection
- **Input Validation**: Robust schema validation preventing malicious inputs

## 🔍 Monitoring & Debugging

### Request Tracking
Every request now includes:
- Unique request ID in response headers (`X-Request-ID`)
- Performance metrics in logs
- Error context for debugging

### Error Logging
Enhanced logging includes:
```
API Error 400: Missing required fields | Request ID: uuid | Endpoint: /api/reports/export | Method: POST
```

### Debug Information
In development mode, responses include:
```json
{
  "debug_info": {
    "endpoint": "/api/reports/export",
    "method": "POST",
    "url": "http://localhost:5000/api/reports/export",
    "user_agent": "Mozilla/5.0..."
  }
}
```

## 🎉 Conclusion

The HTTP 400 error handling improvements provide a robust, secure, and user-friendly error management system. The standardized format ensures consistency across all API endpoints, while the enhanced validation and security features protect against common vulnerabilities.

These improvements significantly enhance both the developer experience and end-user experience when dealing with validation errors and bad requests.