# Firebase Authentication System Documentation

## Overview

The AI-powered report generation platform uses Firebase Authentication for secure user management and API access control. This document provides comprehensive guidance for developers, administrators, and users working with the authentication system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Configuration Guide](#configuration-guide)
3. [API Documentation](#api-documentation)
4. [Frontend Integration](#frontend-integration)
5. [Backend Implementation](#backend-implementation)
6. [Testing Guide](#testing-guide)
7. [Deployment Guide](#deployment-guide)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (React)
    participant FB as Firebase Auth
    participant B as Backend (Flask)
    participant DB as Database

    U->>F: Login Request
    F->>FB: Authenticate User
    FB-->>F: Firebase ID Token
    F->>B: POST /auth/firebase-sync (Bearer token)
    B->>FB: Verify ID Token
    FB-->>B: Decoded Token Data
    B->>DB: Create/Update User
    DB-->>B: User Record
    B-->>F: Success + User Data
    F->>F: Store Auth State
    F->>B: API Request (Bearer token)
    B->>B: Verify Token & Load User
    B-->>F: Protected Resource
```

### Key Components

1. **Firebase Authentication Client** (Frontend)
   - Handles user authentication with Firebase
   - Manages token storage and refresh
   - Provides authentication context to React components

2. **Firebase Admin SDK** (Backend)
   - Verifies Firebase ID tokens
   - Manages Firebase service account credentials
   - Provides secure token validation

3. **Authentication Middleware** (Backend)
   - Intercepts protected route requests
   - Validates Firebase tokens
   - Loads user context for requests

4. **User Management System** (Backend)
   - Syncs Firebase users with local database
   - Manages user profiles and permissions
   - Handles user creation and updates

## Configuration Guide

### Firebase Project Setup

1. **Create Firebase Project**
   ```bash
   # Go to Firebase Console: https://console.firebase.google.com/
   # Create new project or select existing one
   ```

2. **Enable Authentication**
   - Go to Authentication > Sign-in method
   - Enable Email/Password and Google providers
   - Configure authorized domains

3. **Generate Service Account Key**
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Download the JSON file

### Backend Configuration

#### Environment Variables

Create or update `backend/.env`:

```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=tokens/google/service-account.json

# Alternative: Environment Variables (for deployment)
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxx%40your-project.iam.gserviceaccount.com
```

#### Service Account File

Place your Firebase service account JSON file at:
```
backend/tokens/google/your-service-account.json
```

### Frontend Configuration

Update `frontend/.env`:

```bash
# Firebase Configuration
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
VITE_FIREBASE_MEASUREMENT_ID=your-measurement-id

# API Configuration
VITE_API_URL=http://localhost:5000
```

## API Documentation

### Authentication Endpoints

#### POST /auth/firebase-sync

Synchronizes Firebase user with backend database.

**Request:**
```http
POST /auth/firebase-sync
Authorization: Bearer <firebase_id_token>
Content-Type: application/json

{
  "firstName": "John",
  "lastName": "Doe",
  "displayName": "John Doe"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "User synchronized successfully",
  "request_id": "sync_1640995200000",
  "user": {
    "id": 1,
    "email": "john@example.com",
    "firebase_uid": "firebase_uid_123",
    "first_name": "John",
    "last_name": "Doe",
    "username": "john",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T12:00:00Z"
  },
  "sync_metadata": {
    "firebase_uid": "firebase_uid_123",
    "email_verified": true,
    "auth_time": 1640995200,
    "provider": "google.com"
  },
  "sync_timestamp": "2024-01-01T12:00:00Z"
}
```

**Error Responses:**
```json
// 401 - Missing Authorization Header
{
  "error": "No authorization header provided",
  "code": "MISSING_AUTH_HEADER",
  "request_id": "sync_1640995200000"
}

// 401 - Invalid Token
{
  "error": "Invalid or expired Firebase token",
  "code": "INVALID_FIREBASE_TOKEN",
  "request_id": "sync_1640995200000",
  "suggestion": "Please log in again to refresh your authentication token"
}

// 503 - Firebase Not Initialized
{
  "error": "Firebase authentication service unavailable",
  "code": "FIREBASE_NOT_INITIALIZED",
  "request_id": "sync_1640995200000",
  "details": "Firebase Admin SDK initialization failed"
}
```

#### GET /auth/firebase-health

Check Firebase connection health.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "firebase_initialized": true,
  "initialization_attempts": 1,
  "max_attempts": 3,
  "project_id": "your-project-id",
  "has_service_account_path": true,
  "has_private_key": true,
  "app_name": "[DEFAULT]"
}
```

#### GET /auth/firebase-config-validation

Validate Firebase configuration.

**Response (200):**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "configuration_valid": true,
  "validation_details": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "service_account_file": {
      "valid": true,
      "file_exists": true,
      "file_readable": true,
      "valid_json": true,
      "required_fields_present": true,
      "project_id": "your-project-id"
    },
    "environment_variables": {
      "valid": true,
      "missing_variables": [],
      "project_id": "your-project-id"
    },
    "recommendations": []
  }
}
```

#### POST /auth/verify-token

Verify Firebase token utility.

**Request:**
```http
POST /auth/verify-token
Authorization: Bearer <firebase_id_token>
```

**Response (200):**
```json
{
  "valid": true,
  "uid": "firebase_uid_123",
  "email": "john@example.com",
  "email_verified": true
}
```

### Protected Endpoints

All NextGen API endpoints require Firebase authentication:

- `GET /api/v1/nextgen/data-sources`
- `GET /api/v1/nextgen/data-sources/{id}/fields`
- `GET /api/v1/nextgen/templates`
- `POST /api/v1/nextgen/reports`
- And more...

**Authentication Required:**
```http
Authorization: Bearer <firebase_id_token>
```

## Frontend Integration

### FirebaseAuthContext Usage

```typescript
import { useFirebaseAuth } from '../context/FirebaseAuthContext';

function MyComponent() {
  const {
    user,
    isLoading,
    isAuthenticated,
    loginWithEmail,
    loginWithGoogle,
    logout
  } = useFirebaseAuth();

  const handleEmailLogin = async () => {
    try {
      await loginWithEmail('user@example.com', 'password');
      console.log('Login successful');
    } catch (error) {
      console.error('Login failed:', error.message);
    }
  };

  if (isLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <LoginForm />;

  return <div>Welcome, {user?.email}!</div>;
}
```

### Making Authenticated API Calls

```typescript
import axiosInstance from '../services/axiosInstance';

// The axios instance automatically includes Firebase tokens
const fetchDataSources = async () => {
  try {
    const response = await axiosInstance.get('/api/v1/nextgen/data-sources');
    return response.data;
  } catch (error) {
    if (error.response?.status === 401) {
      // Token expired or invalid - user will be redirected to login
      console.log('Authentication required');
    }
    throw error;
  }
};
```

### Error Handling

```typescript
// Listen for authentication events
useEffect(() => {
  const handleAuthError = (event) => {
    console.log('Authentication error:', event.detail);
    // Handle token expiration, show login modal, etc.
  };

  window.addEventListener('auth:token-expired', handleAuthError);
  window.addEventListener('auth:login-required', handleAuthError);

  return () => {
    window.removeEventListener('auth:token-expired', handleAuthError);
    window.removeEventListener('auth:login-required', handleAuthError);
  };
}, []);
```

## Backend Implementation

### Using Authentication Decorators

```python
from app.middleware.firebase_auth import require_firebase_auth, get_current_firebase_user

@app.route('/api/protected-endpoint')
@require_firebase_auth
def protected_endpoint():
    user = get_current_firebase_user()
    return jsonify({
        'message': f'Hello {user.email}',
        'user_id': user.id
    })
```

### Custom Authentication Logic

```python
from app.middleware.firebase_auth import firebase_auth_manager
from flask import request, jsonify

def custom_auth_check():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authentication required'}), 401
    
    token = auth_header.replace('Bearer ', '')
    decoded_token = firebase_auth_manager.verify_token(token)
    
    if not decoded_token:
        return jsonify({'error': 'Invalid token'}), 401
    
    user = firebase_auth_manager.get_or_create_user(decoded_token)
    return user
```

### Health Checks

```python
from app.middleware.firebase_auth import validate_firebase_startup_config

# Check Firebase configuration at startup
if not validate_firebase_startup_config():
    print("⚠️ Firebase configuration issues detected")
    # Handle configuration problems
```

## Testing Guide

### Running Tests

```bash
# Backend unit tests
cd backend
pytest tests/test_firebase_auth.py -v

# Backend integration tests
pytest tests/test_firebase_integration.py -v

# Quick authentication test
python test-auth-fixes.py

# End-to-end test suite
python test-e2e-auth.py
```

### Test Coverage

The test suite covers:
- Firebase Admin SDK initialization
- Token verification and validation
- User creation and synchronization
- Authentication decorators
- Error handling scenarios
- Complete authentication flows
- Configuration validation

### Manual Testing

1. **Start Services:**
   ```bash
   # Backend
   cd backend
   python -m flask run

   # Frontend
   cd frontend
   npm run dev
   ```

2. **Test Authentication Flow:**
   - Navigate to frontend (http://localhost:5173)
   - Attempt to access protected pages
   - Login with email/password or Google
   - Verify API calls work after authentication

3. **Test Error Scenarios:**
   - Try accessing protected endpoints without authentication
   - Test with expired tokens
   - Verify error messages are user-friendly

## Deployment Guide

### Development Environment

1. **Setup Firebase Project** (as described in Configuration Guide)

2. **Install Dependencies:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

3. **Configure Environment Variables** (as described above)

4. **Start Services:**
   ```bash
   # Backend
   python -m flask run

   # Frontend
   npm run dev
   ```

### Production Environment

1. **Environment Variables:**
   - Use environment variables instead of service account files
   - Set `FIREBASE_PRIVATE_KEY` and related variables
   - Ensure proper escaping of private key newlines

2. **Security Considerations:**
   - Use HTTPS for all authentication endpoints
   - Set proper CORS origins
   - Enable Firebase security rules
   - Implement rate limiting

3. **Monitoring:**
   - Monitor authentication success/failure rates
   - Set up alerts for Firebase service issues
   - Track token refresh patterns

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set environment variables
ENV FIREBASE_PROJECT_ID=your-project-id
ENV FIREBASE_PRIVATE_KEY="your-private-key"
ENV FIREBASE_CLIENT_EMAIL=your-client-email

EXPOSE 5000
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
```

## Troubleshooting

### Common Issues

#### 1. Firebase Not Initialized (503 Error)

**Symptoms:**
- `/auth/firebase-health` returns 503
- Authentication endpoints return "Firebase not initialized"

**Solutions:**
1. Check service account file path and permissions
2. Verify environment variables are set correctly
3. Ensure Firebase project ID matches configuration
4. Check server logs for initialization errors

**Debug Commands:**
```bash
# Check configuration
curl http://localhost:5000/auth/firebase-config-validation

# Check health
curl http://localhost:5000/auth/firebase-health
```

#### 2. Invalid Firebase Token (401 Error)

**Symptoms:**
- `/auth/firebase-sync` returns 401 with "INVALID_FIREBASE_TOKEN"
- Protected endpoints return authentication errors

**Solutions:**
1. Verify Firebase client configuration matches project
2. Check if token has expired (Firebase tokens expire in 1 hour)
3. Ensure proper token format in Authorization header
4. Verify Firebase project settings

**Debug Steps:**
```bash
# Test token verification
curl -X POST http://localhost:5000/auth/verify-token \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. User Sync Failures (500 Error)

**Symptoms:**
- `/auth/firebase-sync` returns 500
- Users not created in database

**Solutions:**
1. Check database connectivity
2. Verify user model schema matches database
3. Check for database constraint violations
4. Review server logs for specific errors

#### 4. Frontend Authentication Issues

**Symptoms:**
- Users can't log in
- Tokens not stored properly
- API calls fail with 401

**Solutions:**
1. Check Firebase client configuration
2. Verify axios interceptor setup
3. Check browser console for errors
4. Ensure proper error handling in components

### Debug Tools

#### Backend Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check Firebase manager status
from app.middleware.firebase_auth import firebase_auth_manager
status = firebase_auth_manager.get_initialization_status()
print(status)

# Validate configuration
config_summary = firebase_auth_manager.validate_configuration()
print(config_summary)
```

#### Frontend Debugging

```javascript
// Check authentication state
console.log('Auth state:', useFirebaseAuth());

// Check stored tokens
console.log('Firebase token:', localStorage.getItem('firebaseToken'));

// Check axios configuration
console.log('Axios headers:', axiosInstance.defaults.headers.common);
```

### Performance Monitoring

#### Key Metrics

- Authentication success rate
- Token verification latency
- User sync performance
- Error frequency by type
- Database connection pool status

#### Monitoring Setup

```python
# Add metrics collection
from prometheus_client import Counter, Histogram

auth_attempts = Counter('firebase_auth_attempts_total', 'Total authentication attempts')
auth_duration = Histogram('firebase_auth_duration_seconds', 'Authentication duration')

@auth_duration.time()
def authenticate_user():
    auth_attempts.inc()
    # Authentication logic
```

### Support and Resources

- **Firebase Documentation:** https://firebase.google.com/docs/auth
- **Flask Documentation:** https://flask.palletsprojects.com/
- **React Firebase Hooks:** https://github.com/CSFrequency/react-firebase-hooks
- **Project Repository:** [Your repository URL]
- **Issue Tracker:** [Your issue tracker URL]

For additional support, please check the troubleshooting guide or create an issue in the project repository.