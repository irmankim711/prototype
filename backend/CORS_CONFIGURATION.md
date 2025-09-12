# CORS Configuration for NextGen API

## Overview
This document outlines the CORS configuration implemented for your NextGen API endpoints to resolve cross-origin request issues.

## Current Configuration

### Environment Variables (env.development)
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:5174
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-Requested-With,x-request-id
CORS_EXPOSE_HEADERS=Content-Type,Authorization
CORS_SUPPORTS_CREDENTIALS=true
CORS_MAX_AGE=3600
```

### Flask-CORS Configuration
The application now includes comprehensive CORS support:

1. **Global CORS**: Applied to all API routes
2. **Specific Route Coverage**: 
   - `/api/*` - All API routes
   - `/api/v1/*` - NextGen routes (explicitly covered)
   - `/health*` - Health check endpoints
   - `/auth/*` - Authentication endpoints

3. **NextGen Endpoints with CORS**:
   - `GET /api/v1/nextgen/data-sources`
   - `GET /api/v1/nextgen/data-sources/:id/fields`
   - `GET /api/v1/nextgen/templates`
   - `GET /api/v1/nextgen/cors-test` (for testing)

## CORS Headers Applied

### Preflight Response (OPTIONS)
- `Access-Control-Allow-Origin`: Origin-specific or wildcard
- `Access-Control-Allow-Methods`: GET, POST, PUT, DELETE, OPTIONS
- `Access-Control-Allow-Headers`: Content-Type, Authorization, X-Requested-With, x-request-id
- `Access-Control-Allow-Credentials`: true
- `Access-Control-Max-Age`: 3600

### Actual Response
- `Access-Control-Allow-Origin`: Origin-specific or wildcard
- `Access-Control-Allow-Credentials`: true
- `Access-Control-Allow-Methods`: GET, POST, PUT, DELETE, OPTIONS
- `Access-Control-Allow-Headers`: Content-Type, Authorization, X-Requested-With, x-request-id
- `Access-Control-Max-Age`: 3600

## Testing CORS Configuration

### 1. Test Script
Run the provided test script to verify CORS configuration:
```bash
cd backend
python test_cors_config.py
```

### 2. Manual Testing
Test CORS headers using curl:

```bash
# Test preflight request
curl -X OPTIONS \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  http://localhost:5000/api/v1/nextgen/data-sources

# Test actual request
curl -X GET \
  -H "Origin: http://localhost:5173" \
  http://localhost:5000/api/v1/nextgen/cors-test
```

### 3. Browser Testing
Open browser console and test:
```javascript
fetch('http://localhost:5000/api/v1/nextgen/cors-test', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## Frontend Integration

### 1. API Service Configuration
Ensure your frontend API service includes:
```typescript
const apiConfig = {
  baseURL: 'http://localhost:5000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}` // if using JWT
  }
};
```

### 2. CORS Headers in Requests
Your frontend should automatically include:
- `Origin: http://localhost:5173`
- `Access-Control-Request-Method` (for preflight)
- `Access-Control-Request-Headers` (for preflight)

## Troubleshooting

### Common Issues

1. **CORS Error: No 'Access-Control-Allow-Origin' header**
   - Check if server is running
   - Verify CORS_ORIGINS includes your frontend URL
   - Check browser console for detailed error

2. **Preflight Request Fails**
   - Ensure OPTIONS method is handled
   - Check CORS_METHODS includes OPTIONS
   - Verify CORS_ALLOW_HEADERS includes required headers

3. **Credentials Not Sent**
   - Set `withCredentials: true` in frontend
   - Ensure CORS_SUPPORTS_CREDENTIALS is true
   - Check Access-Control-Allow-Credentials header

### Debug Steps

1. **Check Server Logs**
   ```bash
   cd backend
   python run.py
   ```

2. **Verify Environment Variables**
   ```bash
   cd backend
   python -c "from app.core.config import get_cors_config; print(get_cors_config())"
   ```

3. **Test Individual Endpoints**
   Use the test script or manual testing methods above

## Security Considerations

### Development vs Production

- **Development**: Allows multiple localhost origins
- **Production**: Should restrict to specific domains
- **Credentials**: Always enabled for authentication

### Headers Allowed
- `Content-Type`: Required for JSON requests
- `Authorization`: Required for JWT authentication
- `X-Requested-With`: Standard AJAX header
- `x-request-id`: For request tracking

## Next Steps

1. **Test the configuration** using the provided test script
2. **Verify frontend integration** works without CORS errors
3. **Monitor server logs** for any CORS-related issues
4. **Update production configuration** when deploying

## Support

If you encounter CORS issues:
1. Check server logs for error messages
2. Verify environment variable configuration
3. Test with the provided test script
4. Check browser console for detailed error information
