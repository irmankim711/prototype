# Error Investigation Guide for /api/v1/nextgen/excel/generate-report

## Error Details from Railway
- **Timestamp**: 2025-11-03T08:08:07.922015157Z
- **Status**: 500 Internal Server Error
- **Duration**: 4183ms (~4.2 seconds)
- **Client IP**: 121.121.60.200
- **Region**: asia-southeast1-eqsg3a

## Most Likely Root Causes (In Priority Order)

### 1. Firebase Authentication Failure (HIGHEST PROBABILITY)
**Location**: `backend/app/decorators.py:97-102`

```python
except Exception as e:
    current_app.logger.error(f"Authentication error: {str(e)}")
    return jsonify({
        'error': 'Authentication failed',
        'code': 'AUTH_ERROR'
    }), 500
```

**Symptoms**:
- Returns 500 instead of 401/403
- Happens before any endpoint logic runs
- Duration: ~4 seconds (consistent with Firebase token verification timeout)

**How to Check**:
1. Check Railway logs for "Authentication error" messages
2. Verify Firebase is initialized: Look for "Firebase not initialized for authentication"
3. Check if the Authorization header is being sent properly

**Fix**:
```python
# In decorators.py, change the exception handler to return 401 instead of 500
except Exception as e:
    current_app.logger.error(f"Authentication error: {str(e)}")
    import traceback
    current_app.logger.error(traceback.format_exc())
    return jsonify({
        'error': 'Authentication failed',
        'code': 'AUTH_ERROR',
        'details': str(e)  # Add details for debugging
    }), 401  # Changed from 500 to 401
```

### 2. Missing or Invalid Request Data
**Location**: `backend/app/routes/nextgen_report_builder.py:1040-1061`

**Symptoms**:
- Missing `excelFilePath` or `templateId` in request body
- Returns 400 error (but could return 500 if JSON parsing fails)

**How to Check**:
1. Look for logs: "No data provided in request" or "Missing required fields"
2. Check the request payload sent from frontend

**Fix**: Already has proper error handling, returns 400

### 3. Excel File Not Found on Server
**Location**: `backend/app/routes/nextgen_report_builder.py:1063-1091`

**Symptoms**:
- The file path from frontend doesn't exist on Railway server
- Returns 400 with "Excel file not found"

**Note**: This should return 400, not 500, so less likely

### 4. Template Lookup Failure
**Location**: `backend/app/routes/nextgen_report_builder.py:1176-1278`

**Symptoms**:
- Template not found in database
- Template file not found on filesystem
- Returns 404 with "Template not found"

**Note**: This should return 404, not 500, so less likely

### 5. Database Connection/Query Errors
**Location**: `backend/app/routes/nextgen_report_builder.py:1791-1907`

**Symptoms**:
- SQL insert fails
- Database connection timeout
- Returns 500 with database error details

**How to Check**:
1. Look for "Database error creating report" in logs
2. Check Railway database connection status

## Debugging Steps (Do These in Order)

### Step 1: Check Railway Application Logs
```bash
# SSH into Railway or use Railway CLI
railway logs

# Look for these specific patterns:
# 1. "Authentication error"
# 2. "Firebase not initialized"
# 3. "No data provided in request"
# 4. "Excel file not found"
# 5. "Template not found"
# 6. "Database error"
```

### Step 2: Check Frontend Request
Verify the frontend is sending:
1. Valid Authorization header with Firebase token
2. Valid JSON body with `excelFilePath` and `templateId`
3. The Excel file path actually exists on the server

### Step 3: Test Authentication Separately
```bash
# Test if Firebase auth is working
curl -X POST https://backend-test-6a78.up.railway.app/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"excelFilePath": "/test", "templateId": "1"}'
```

### Step 4: Check Environment Variables
Verify these are set in Railway:
- `FIREBASE_PROJECT_ID`
- `FIREBASE_PRIVATE_KEY`
- `FIREBASE_CLIENT_EMAIL`
- Database connection variables

## Recommended Immediate Fix

Add enhanced logging to the authentication decorator to capture the exact error:

```python
# In backend/app/decorators.py:97-102
except Exception as e:
    import traceback
    tb = traceback.format_exc()

    # Log comprehensive error details
    current_app.logger.error("=" * 80)
    current_app.logger.error("AUTHENTICATION ERROR DETAILS")
    current_app.logger.error("=" * 80)
    current_app.logger.error(f"Error Type: {type(e).__name__}")
    current_app.logger.error(f"Error Message: {str(e)}")
    current_app.logger.error(f"Request URL: {request.url}")
    current_app.logger.error(f"Request Method: {request.method}")
    current_app.logger.error(f"Request Headers: {dict(request.headers)}")
    current_app.logger.error(f"Full Traceback:\n{tb}")
    current_app.logger.error("=" * 80)

    return jsonify({
        'error': 'Authentication failed',
        'code': 'AUTH_ERROR',
        'error_type': type(e).__name__,
        'timestamp': datetime.now().isoformat()
    }), 401  # Return 401 instead of 500
```

## Next Steps

1. **Apply the enhanced logging fix** to `decorators.py`
2. **Deploy to Railway** and reproduce the error
3. **Check Railway logs** for the detailed error information
4. **Based on the logs**, apply the specific fix for the root cause

## Contact Information

If you need help interpreting the logs, provide:
1. Full Railway log output around the error timestamp
2. Frontend request details (headers, body)
3. Any related error messages from the browser console
