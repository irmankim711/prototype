# Firebase Authentication Troubleshooting Guide

## Quick Diagnosis Checklist

Before diving into specific issues, run through this quick checklist:

### ✅ System Health Check

```bash
# 1. Check if services are running
curl http://localhost:5000/health          # Backend health
curl http://localhost:5173                 # Frontend accessibility

# 2. Check Firebase health
curl http://localhost:5000/auth/firebase-health

# 3. Validate Firebase configuration
curl http://localhost:5000/auth/firebase-config-validation

# 4. Run automated tests
python test-auth-fixes.py                  # Quick backend test
python test-e2e-auth.py                   # Complete system test
```

### 🔍 Quick Debug Commands

```bash
# Check environment variables
echo $FIREBASE_PROJECT_ID
echo $FIREBASE_SERVICE_ACCOUNT_PATH

# Check service account file
ls -la backend/tokens/google/
cat backend/tokens/google/your-service-account.json | jq .project_id

# Check logs
tail -f backend/logs/app.log              # If logging to file
```

## Common Error Scenarios

### 1. 500 Internal Server Error in `/auth/firebase-sync`

**Error Message:**
```json
{
  "error": "Internal server error",
  "code": "INTERNAL_SERVER_ERROR",
  "request_id": "sync_1640995200000"
}
```

**Root Causes & Solutions:**

#### A. Firebase Admin SDK Not Initialized

**Symptoms:**
- Server logs show "Firebase not initialized"
- `/auth/firebase-health` returns 503

**Debug Steps:**
```bash
# Check Firebase health
curl http://localhost:5000/auth/firebase-health

# Check configuration validation
curl http://localhost:5000/auth/firebase-config-validation
```

**Solutions:**

1. **Missing Service Account File:**
   ```bash
   # Check if file exists
   ls -la backend/tokens/google/

   # Verify path in .env
   grep FIREBASE_SERVICE_ACCOUNT_PATH backend/.env
   ```

2. **Invalid Service Account File:**
   ```bash
   # Validate JSON format
   cat backend/tokens/google/your-file.json | jq .

   # Check required fields
   cat backend/tokens/google/your-file.json | jq 'keys'
   # Should include: type, project_id, private_key, client_email
   ```

3. **Environment Variables Missing:**
   ```bash
   # Check required variables
   echo "Project ID: $FIREBASE_PROJECT_ID"
   echo "Private Key exists: $([ -n "$FIREBASE_PRIVATE_KEY" ] && echo "Yes" || echo "No")"
   echo "Client Email: $FIREBASE_CLIENT_EMAIL"
   ```

4. **File Permissions:**
   ```bash
   # Fix file permissions
   chmod 600 backend/tokens/google/your-file.json
   chown $USER:$USER backend/tokens/google/your-file.json
   ```

#### B. Database Connection Issues

**Symptoms:**
- User creation fails
- Database rollback messages in logs

**Debug Steps:**
```python
# Test database connection
from app import create_app, db
app = create_app()
with app.app_context():
    try:
        db.engine.execute('SELECT 1')
        print("Database connection OK")
    except Exception as e:
        print(f"Database error: {e}")
```

**Solutions:**
1. Check database URL in `.env`
2. Ensure database server is running
3. Verify database permissions
4. Check for schema migrations needed

#### C. Token Verification Failures

**Symptoms:**
- "Invalid or expired token" errors
- Token verification returns None

**Debug Steps:**
```bash
# Test token verification directly
curl -X POST http://localhost:5000/auth/verify-token \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

**Solutions:**
1. Verify Firebase project configuration matches
2. Check token expiration (Firebase tokens expire in 1 hour)
3. Ensure proper token format in Authorization header

### 2. 401 Unauthorized Errors in Protected Endpoints

**Error Message:**
```json
{
  "error": "Authentication required",
  "code": "MISSING_AUTH_HEADER",
  "request_id": "auth_1640995200000"
}
```

**Root Causes & Solutions:**

#### A. Missing Authorization Header

**Debug Steps:**
```bash
# Test with proper header
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/v1/nextgen/data-sources
```

**Solutions:**
1. Ensure frontend sends Authorization header
2. Check axios interceptor configuration
3. Verify token storage in localStorage

#### B. Invalid Token Format

**Common Issues:**
- Missing "Bearer " prefix
- Token corruption during storage
- Wrong token type (JWT vs Firebase)

**Debug Steps:**
```javascript
// Check stored token
console.log('Stored token:', localStorage.getItem('firebaseToken'));

// Check axios headers
console.log('Axios headers:', axiosInstance.defaults.headers.common);
```

**Solutions:**
```javascript
// Ensure proper token format
axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

#### C. Token Expiration

**Symptoms:**
- Authentication works initially, then fails
- "Token expired" errors in logs

**Solutions:**
1. Implement automatic token refresh
2. Check token refresh interval (should be < 1 hour)
3. Handle token expiration gracefully

### 3. Frontend Authentication Issues

#### A. Firebase Client Configuration

**Symptoms:**
- Firebase authentication fails
- "Firebase app not initialized" errors

**Debug Steps:**
```javascript
// Check Firebase config
import { auth } from '../config/firebase';
console.log('Firebase app:', auth.app);
console.log('Firebase config:', auth.app.options);
```

**Solutions:**
1. Verify Firebase client configuration in `.env`
2. Check Firebase project settings match
3. Ensure Firebase SDK is properly initialized

#### B. Authentication State Management

**Symptoms:**
- User state not persisting
- Authentication context issues
- Page refresh loses authentication

**Debug Steps:**
```javascript
// Check authentication context
const authContext = useFirebaseAuth();
console.log('Auth context:', authContext);

// Check Firebase auth state
import { auth } from '../config/firebase';
console.log('Firebase user:', auth.currentUser);
```

**Solutions:**
1. Ensure FirebaseAuthProvider wraps app
2. Check authentication state persistence
3. Verify token storage and retrieval

#### C. API Call Failures

**Symptoms:**
- Authenticated API calls return 401
- Axios interceptor not working

**Debug Steps:**
```javascript
// Check axios configuration
console.log('Axios base URL:', axiosInstance.defaults.baseURL);
console.log('Axios headers:', axiosInstance.defaults.headers);

// Test API call manually
axiosInstance.get('/api/v1/nextgen/data-sources')
  .then(response => console.log('Success:', response))
  .catch(error => console.log('Error:', error.response));
```

**Solutions:**
1. Verify axios interceptor setup
2. Check API base URL configuration
3. Ensure proper error handling

### 4. Configuration Issues

#### A. Environment Variables

**Common Problems:**
- Variables not loaded
- Incorrect variable names
- Missing quotes for complex values

**Debug Steps:**
```bash
# Backend environment check
cd backend
python -c "import os; print('FIREBASE_PROJECT_ID:', os.getenv('FIREBASE_PROJECT_ID'))"

# Frontend environment check
cd frontend
echo "VITE_FIREBASE_PROJECT_ID: $VITE_FIREBASE_PROJECT_ID"
```

**Solutions:**
1. Check `.env` file exists and is properly formatted
2. Restart services after environment changes
3. Verify environment variable names (VITE_ prefix for frontend)

#### B. Firebase Project Configuration

**Symptoms:**
- Authentication works but API calls fail
- Project ID mismatches

**Debug Steps:**
```bash
# Check Firebase project consistency
grep -r "project.*id" backend/.env frontend/.env
cat backend/tokens/google/service-account.json | jq .project_id
```

**Solutions:**
1. Ensure all configurations use same project ID
2. Verify Firebase project settings
3. Check service account belongs to correct project

## Debugging Tools and Techniques

### Backend Debugging

#### Enable Debug Logging

```python
# In your Flask app
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in specific modules
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

#### Firebase Manager Debug

```python
# Check Firebase manager status
from app.middleware.firebase_auth import firebase_auth_manager

# Get initialization status
status = firebase_auth_manager.get_initialization_status()
print("Firebase Status:", status)

# Validate configuration
config = firebase_auth_manager.validate_configuration()
print("Configuration:", config)

# Force reinitialization
success = firebase_auth_manager.force_reinitialize()
print("Reinitialization:", success)
```

#### Database Debug

```python
# Check user creation
from app.models.production.user_models import User
from app import db

# List users
users = User.query.all()
print(f"Total users: {len(users)}")

# Check specific user
user = User.query.filter_by(email='test@example.com').first()
print(f"User: {user}")
```

### Frontend Debugging

#### Authentication Context Debug

```javascript
// Add to your component
const authContext = useFirebaseAuth();
console.log('Authentication State:', {
  user: authContext.user,
  isLoading: authContext.isLoading,
  isAuthenticated: authContext.isAuthenticated,
  firebaseUser: authContext.firebaseUser
});
```

#### Token Debug

```javascript
// Check token storage
console.log('Tokens:', {
  firebaseToken: localStorage.getItem('firebaseToken'),
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken')
});

// Check axios configuration
console.log('Axios Config:', {
  baseURL: axiosInstance.defaults.baseURL,
  headers: axiosInstance.defaults.headers.common
});
```

#### Network Debug

```javascript
// Add request/response logging
axiosInstance.interceptors.request.use(request => {
  console.log('Request:', request);
  return request;
});

axiosInstance.interceptors.response.use(
  response => {
    console.log('Response:', response);
    return response;
  },
  error => {
    console.log('Error:', error.response);
    return Promise.reject(error);
  }
);
```

### Network Debugging

#### Check API Endpoints

```bash
# Test authentication endpoints
curl -v http://localhost:5000/auth/firebase-health
curl -v http://localhost:5000/auth/firebase-config-validation

# Test protected endpoints (should return 401)
curl -v http://localhost:5000/api/v1/nextgen/data-sources

# Test with authentication
curl -v -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/v1/nextgen/data-sources
```

#### CORS Issues

```bash
# Test CORS preflight
curl -v -X OPTIONS \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  http://localhost:5000/api/v1/nextgen/data-sources
```

## Performance Debugging

### Slow Authentication

**Symptoms:**
- Long delays during login
- Timeout errors

**Debug Steps:**
1. Check Firebase service response times
2. Monitor database query performance
3. Profile token verification operations

**Solutions:**
1. Optimize database queries
2. Implement connection pooling
3. Add caching for frequently accessed data

### Memory Issues

**Symptoms:**
- Increasing memory usage
- Application crashes

**Debug Steps:**
1. Monitor memory usage patterns
2. Check for memory leaks in token storage
3. Profile authentication operations

**Solutions:**
1. Implement proper cleanup in useEffect hooks
2. Clear unused tokens from storage
3. Optimize authentication state management

## Production Debugging

### Log Analysis

```bash
# Search for authentication errors
grep -i "auth.*error" /var/log/app.log

# Find specific error patterns
grep "FIREBASE_TOKEN_INVALID" /var/log/app.log

# Monitor authentication success rate
grep "authentication successful" /var/log/app.log | wc -l
```

### Monitoring Setup

```python
# Add metrics collection
from prometheus_client import Counter, Histogram, Gauge

# Authentication metrics
auth_attempts = Counter('firebase_auth_attempts_total', 
                       'Total authentication attempts', 
                       ['status'])

auth_duration = Histogram('firebase_auth_duration_seconds',
                         'Authentication duration')

active_users = Gauge('firebase_active_users',
                    'Number of active authenticated users')

# Use in authentication code
@auth_duration.time()
def authenticate_user():
    try:
        # Authentication logic
        auth_attempts.labels(status='success').inc()
        active_users.inc()
    except Exception as e:
        auth_attempts.labels(status='failure').inc()
        raise
```

### Health Monitoring

```bash
# Create health check script
#!/bin/bash
# health-check.sh

echo "Checking authentication system health..."

# Check Firebase health
FIREBASE_HEALTH=$(curl -s http://localhost:5000/auth/firebase-health | jq -r '.status')
echo "Firebase Health: $FIREBASE_HEALTH"

# Check authentication endpoints
AUTH_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/nextgen/data-sources)
echo "Auth Endpoint Status: $AUTH_TEST"

# Check configuration
CONFIG_VALID=$(curl -s http://localhost:5000/auth/firebase-config-validation | jq -r '.configuration_valid')
echo "Configuration Valid: $CONFIG_VALID"

if [ "$FIREBASE_HEALTH" = "healthy" ] && [ "$AUTH_TEST" = "401" ] && [ "$CONFIG_VALID" = "true" ]; then
    echo "✅ Authentication system is healthy"
    exit 0
else
    echo "❌ Authentication system has issues"
    exit 1
fi
```

## Emergency Recovery Procedures

### Complete Authentication Reset

If authentication is completely broken:

1. **Stop Services:**
   ```bash
   # Stop backend and frontend
   pkill -f "flask run"
   pkill -f "npm run dev"
   ```

2. **Reset Configuration:**
   ```bash
   # Backup current config
   cp backend/.env backend/.env.backup
   cp frontend/.env frontend/.env.backup

   # Reset to known good configuration
   # (Use your backup or template files)
   ```

3. **Clear Authentication Data:**
   ```bash
   # Clear browser storage (in browser console)
   localStorage.clear();
   sessionStorage.clear();

   # Clear server-side sessions if applicable
   ```

4. **Reinitialize Firebase:**
   ```bash
   # Force Firebase reinitialization
   curl -X POST http://localhost:5000/auth/firebase-reinitialize
   ```

5. **Restart Services:**
   ```bash
   # Start backend
   cd backend && python -m flask run &

   # Start frontend
   cd frontend && npm run dev &
   ```

6. **Verify Recovery:**
   ```bash
   # Run health checks
   python test-e2e-auth.py
   ```

### Database Recovery

If user data is corrupted:

1. **Backup Database:**
   ```bash
   # For SQLite
   cp backend/app.db backend/app.db.backup

   # For PostgreSQL
   pg_dump your_database > backup.sql
   ```

2. **Reset User Tables:**
   ```sql
   -- Clear user data (be careful!)
   DELETE FROM user_sessions;
   DELETE FROM user_tokens;
   -- Don't delete users unless absolutely necessary
   ```

3. **Reinitialize Schema:**
   ```bash
   cd backend
   flask db upgrade
   ```

## Getting Help

### Information to Collect

When reporting authentication issues, include:

1. **System Information:**
   - Operating system
   - Python version
   - Node.js version
   - Browser version (for frontend issues)

2. **Configuration:**
   - Environment variables (sanitized)
   - Firebase project settings
   - Service account file structure (without sensitive data)

3. **Error Details:**
   - Complete error messages
   - Request/response headers
   - Server logs
   - Browser console logs

4. **Reproduction Steps:**
   - Exact steps to reproduce the issue
   - Expected vs actual behavior
   - Frequency of the issue

### Debug Information Script

```bash
#!/bin/bash
# collect-debug-info.sh

echo "=== Authentication Debug Information ==="
echo "Date: $(date)"
echo "System: $(uname -a)"

echo -e "\n=== Service Status ==="
curl -s http://localhost:5000/auth/firebase-health | jq .
curl -s http://localhost:5000/auth/firebase-config-validation | jq .

echo -e "\n=== Environment Variables ==="
echo "FIREBASE_PROJECT_ID: ${FIREBASE_PROJECT_ID:-'Not set'}"
echo "FIREBASE_SERVICE_ACCOUNT_PATH: ${FIREBASE_SERVICE_ACCOUNT_PATH:-'Not set'}"
echo "VITE_FIREBASE_PROJECT_ID: ${VITE_FIREBASE_PROJECT_ID:-'Not set'}"

echo -e "\n=== File Status ==="
if [ -f "$FIREBASE_SERVICE_ACCOUNT_PATH" ]; then
    echo "Service account file: EXISTS"
    echo "File size: $(stat -c%s "$FIREBASE_SERVICE_ACCOUNT_PATH") bytes"
    echo "Project ID in file: $(cat "$FIREBASE_SERVICE_ACCOUNT_PATH" | jq -r .project_id)"
else
    echo "Service account file: NOT FOUND"
fi

echo -e "\n=== Recent Logs ==="
tail -20 backend/logs/app.log 2>/dev/null || echo "No log file found"

echo -e "\n=== Test Results ==="
python test-auth-fixes.py 2>&1 | tail -10
```

### Support Channels

- **Documentation:** Check the main authentication documentation
- **Issue Tracker:** Create detailed bug reports
- **Community:** Ask questions in project discussions
- **Emergency:** Contact system administrators for production issues

Remember: Always sanitize sensitive information (tokens, private keys, passwords) before sharing debug information!