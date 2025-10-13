# Comprehensive Security Implementation

This document outlines the comprehensive security implementation for the application, including CSRF protection, security headers, and secure session management.

## 🛡️ Security Features Implemented

### 1. CSRF Protection
- **Enhanced CSRF Middleware**: Redis-backed token storage with in-memory fallback
- **Double Submit Pattern**: Both header and cookie validation for maximum security
- **Automatic Token Management**: Generation, validation, and refresh
- **Frontend Integration**: Automatic token inclusion in all API calls

### 2. Security Headers
- **Content Security Policy (CSP)**: Comprehensive policy with nonce support
- **Strict Transport Security (HSTS)**: HTTPS enforcement
- **X-Frame-Options**: Clickjacking protection
- **X-Content-Type-Options**: MIME type sniffing protection
- **X-XSS-Protection**: XSS protection
- **Referrer Policy**: Control over referrer information
- **Permissions Policy**: Feature policy control
- **Cross-Origin Policies**: Modern security policies

### 3. Secure Session Management
- **Secure Cookies**: HttpOnly, Secure, and SameSite attributes
- **Session Signing**: Cryptographic session validation
- **Automatic Expiry**: Configurable session lifetime

### 4. Enhanced CORS Configuration
- **Production-Ready**: Environment-specific CORS policies
- **Credential Support**: Secure cross-origin requests
- **Header Validation**: Comprehensive header security

## 🚀 Quick Start

### Backend Setup

1. **Install Dependencies**
```bash
pip install redis flask-cors
```

2. **Environment Configuration**
```bash
# Copy development.env to .env
cp development.env .env

# For production, use production.env
cp production.env .env
```

3. **Redis Setup** (for CSRF token storage)
```bash
# Install Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

4. **Register CSRF Blueprint**
```python
# In your Flask app
from app.routes.csrf import csrf_bp
app.register_blueprint(csrf_bp, url_prefix='/api/csrf')
```

### Frontend Setup

1. **Install Dependencies**
```bash
npm install
```

2. **Environment Configuration**
```bash
# Copy development.env to .env.development
cp development.env .env.development

# For production, use production.env
cp production.env .env.production
```

3. **Import CSRF Service**
```typescript
import csrfService from './services/csrfService';
```

## 📖 Usage Examples

### Backend Usage

#### 1. Using Enhanced Security Middleware

```python
from app.middleware.enhanced_security import (
    EnhancedCSRFMiddleware,
    EnhancedSecurityHeadersMiddleware,
    SecureSessionMiddleware
)

def create_app():
    app = Flask(__name__)
    
    # Initialize security middleware
    csrf_middleware = EnhancedCSRFMiddleware(app)
    security_headers = EnhancedSecurityHeadersMiddleware(app)
    session_middleware = SecureSessionMiddleware(app)
    
    # Store middleware instances for access
    app.csrf_middleware = csrf_middleware
    
    return app
```

#### 2. CSRF Token Generation

```python
from app.middleware.enhanced_security import EnhancedCSRFMiddleware

@app.route('/api/csrf/token')
@jwt_required()
def get_csrf_token():
    user_id = get_jwt_identity()
    token = csrf_middleware.generate_csrf_token(user_id)
    return jsonify({'csrf_token': token})
```

#### 3. CSRF Validation

```python
from app.middleware.enhanced_security import require_csrf_token

@app.route('/api/protected-endpoint', methods=['POST'])
@jwt_required()
@require_csrf_token
def protected_endpoint():
    # CSRF validation is automatic
    return jsonify({'message': 'Success'})
```

### Frontend Usage

#### 1. Basic CSRF Token Usage

```typescript
import { useCSRF } from '../hooks/useCSRF';

function MyForm() {
  const { csrfToken, isLoading, error } = useCSRF();

  const handleSubmit = async (formData: FormData) => {
    if (csrfToken) {
      formData.append('csrf_token', csrfToken);
    }
    
    const response = await fetch('/api/submit', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
  };

  if (isLoading) return <div>Loading security...</div>;
  if (error) return <div>Security error: {error}</div>;

  return (
    <form onSubmit={handleSubmit}>
      <CSRFTokenInput />
      {/* Your form fields */}
    </form>
  );
}
```

#### 2. Using CSRF Service Directly

```typescript
import csrfService from '../services/csrfService';

async function submitData(data: any) {
  try {
    // Ensure we have a valid CSRF token
    const token = await csrfService.ensureValidToken();
    
    const response = await fetch('/api/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token
      },
      body: JSON.stringify(data),
      credentials: 'include'
    });
    
    return response.json();
  } catch (error) {
    console.error('Submission failed:', error);
  }
}
```

#### 3. Form with CSRF Protection

```typescript
import { CSRFTokenInput, withCSRFProtection } from '../components/CSRFTokenInput';

// Basic usage
function SimpleForm() {
  return (
    <form>
      <CSRFTokenInput showErrors={true} />
      <input type="text" name="username" />
      <button type="submit">Submit</button>
    </form>
  );
}

// Advanced usage with HOC
const ProtectedForm = withCSRFProtection(function FormComponent() {
  return (
    <form>
      <input type="text" name="username" />
      <button type="submit">Submit</button>
    </form>
  );
});
```

#### 4. API Service Integration

```typescript
import { api } from '../services/api-new';

// CSRF tokens are automatically included
async function createUser(userData: any) {
  const response = await api.post('/users', userData);
  return response.data;
}

// For custom requests
async function customRequest(url: string, data: any) {
  const csrfToken = await csrfService.getToken();
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken
    },
    body: JSON.stringify(data),
    credentials: 'include'
  });
  
  return response.json();
}
```

## ⚙️ Configuration

### Environment Variables

#### CSRF Configuration
```bash
# Enable/disable CSRF protection
CSRF_ENABLE_CSRF_PROTECTION=true

# Token configuration
CSRF_CSRF_TOKEN_EXPIRY=3600
CSRF_CSRF_TOKEN_LENGTH=64
CSRF_CSRF_HEADER_NAME=X-CSRF-Token
CSRF_CSRF_COOKIE_NAME=csrf_token

# Security settings
CSRF_CSRF_DOUBLE_SUBMIT=true
CSRF_CSRF_SAME_SITE=Strict
CSRF_CSRF_SECURE=true
CSRF_CSRF_HTTP_ONLY=false
```

#### Security Headers
```bash
# Enable security headers
SECURITY_ENABLE_SECURITY_HEADERS=true
SECURITY_ENABLE_CSP=true
SECURITY_ENABLE_HSTS=true

# CSP Policy
SECURITY_CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline';"

# HSTS Configuration
SECURITY_HSTS_MAX_AGE=31536000
SECURITY_HSTS_INCLUDE_SUBDOMAINS=true
```

#### Session Configuration
```bash
# Secure session settings
SESSION_SESSION_COOKIE_SECURE=true
SESSION_SESSION_COOKIE_HTTPONLY=true
SESSION_SESSION_COOKIE_SAMESITE=Strict
SESSION_SESSION_COOKIE_MAX_AGE=3600
```

### Production Configuration

For production environments, use the `production.env` file which includes:

- **HTTPS Enforcement**: All security features enabled
- **Strict CORS**: Limited to specific domains
- **Enhanced Monitoring**: Sentry integration
- **Rate Limiting**: Production-grade rate limiting
- **SSL/TLS**: Certificate configuration

## 🔒 Security Best Practices

### 1. Token Management
- **Automatic Refresh**: Tokens refresh before expiry
- **Secure Storage**: Tokens stored in memory with Redis backup
- **Validation**: Comprehensive token validation

### 2. Headers Security
- **Comprehensive Coverage**: All major security headers implemented
- **Configurable Policies**: Environment-specific security policies
- **Modern Standards**: Latest security header implementations

### 3. Session Security
- **Secure Cookies**: HttpOnly, Secure, and SameSite attributes
- **Automatic Expiry**: Configurable session lifetime
- **Cryptographic Signing**: Session integrity validation

### 4. CORS Security
- **Origin Validation**: Strict origin checking
- **Credential Support**: Secure cross-origin requests
- **Header Security**: Comprehensive header validation

## 🧪 Testing

### Backend Testing

```python
import pytest
from app.middleware.enhanced_security import EnhancedCSRFMiddleware

def test_csrf_token_generation():
    app = create_test_app()
    middleware = EnhancedCSRFMiddleware(app)
    
    token = middleware.generate_csrf_token("test_user")
    assert token is not None
    assert len(token) == 128  # 64 bytes = 128 hex chars

def test_csrf_token_validation():
    app = create_test_app()
    middleware = EnhancedCSRFMiddleware(app)
    
    token = middleware.generate_csrf_token("test_user")
    assert middleware._is_valid_csrf_token(token) == True
```

### Frontend Testing

```typescript
import { render, screen } from '@testing-library/react';
import { CSRFTokenInput } from '../components/CSRFTokenInput';

test('renders CSRF token input', () => {
  render(<CSRFTokenInput />);
  const input = screen.getByTestId('csrf-token-input');
  expect(input).toBeInTheDocument();
});

test('shows loading state', () => {
  render(<CSRFTokenInput showLoading={true} />);
  expect(screen.getByText(/Loading CSRF protection/)).toBeInTheDocument();
});
```

## 🚨 Troubleshooting

### Common Issues

#### 1. CSRF Token Validation Fails
- **Check Redis Connection**: Ensure Redis is running and accessible
- **Verify Token Expiry**: Check token lifetime configuration
- **Check CORS**: Ensure CORS is properly configured

#### 2. Security Headers Not Applied
- **Check Configuration**: Verify environment variables are set
- **Middleware Order**: Ensure security middleware is registered early
- **Response Headers**: Check if headers are being overridden

#### 3. Frontend Token Issues
- **Authentication**: Ensure user is authenticated before requesting tokens
- **CORS Credentials**: Verify `withCredentials: true` is set
- **Token Storage**: Check localStorage for token persistence

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Backend
LOG_LEVEL=DEBUG

# Frontend
VITE_DEBUG_API=true
```

## 📚 Additional Resources

- [OWASP CSRF Prevention](https://owasp.org/www-community/attacks/csrf)
- [Security Headers Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security)
- [Flask Security Best Practices](https://flask-security.readthedocs.io/)
- [React Security Guidelines](https://reactjs.org/docs/security.html)

## 🤝 Contributing

When contributing to security features:

1. **Follow Security Guidelines**: Adhere to OWASP recommendations
2. **Test Thoroughly**: Ensure all security features are tested
3. **Document Changes**: Update this README for any modifications
4. **Security Review**: Request security review for major changes

## 📄 License

This security implementation is part of the main project and follows the same license terms.

---

**⚠️ Security Notice**: This implementation provides comprehensive security features, but security is an ongoing process. Regularly update dependencies, monitor security advisories, and conduct security audits.
