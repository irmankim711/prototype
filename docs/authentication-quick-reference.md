# Firebase Authentication Quick Reference

## 🚀 Quick Start

### 1. Check System Health
```bash
# Run this first to check if everything is working
python test-e2e-auth.py
```

### 2. Common Commands
```bash
# Backend health check
curl http://localhost:5000/auth/firebase-health

# Configuration validation
curl http://localhost:5000/auth/firebase-config-validation

# Test protected endpoint (should return 401)
curl http://localhost:5000/api/v1/nextgen/data-sources

# Test with authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/v1/nextgen/data-sources
```

## 🔧 Configuration Checklist

### Backend (.env)
```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=tokens/google/service-account.json
```

### Frontend (.env)
```bash
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_API_URL=http://localhost:5000
```

## 🐛 Quick Debugging

### Error: 500 in firebase-sync
```bash
# Check Firebase initialization
curl http://localhost:5000/auth/firebase-health

# Check service account file
ls -la backend/tokens/google/
cat backend/tokens/google/your-file.json | jq .project_id
```

### Error: 401 in protected endpoints
```bash
# Check if authentication is required (should return 401)
curl http://localhost:5000/api/v1/nextgen/data-sources

# Test token verification
curl -X POST http://localhost:5000/auth/verify-token \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend not authenticating
```javascript
// Check in browser console
console.log('Auth context:', useFirebaseAuth());
console.log('Firebase token:', localStorage.getItem('firebaseToken'));
console.log('Axios headers:', axiosInstance.defaults.headers.common);
```

## 📝 Code Examples

### Backend: Protected Route
```python
from app.middleware.firebase_auth import require_firebase_auth, get_current_firebase_user

@app.route('/api/my-endpoint')
@require_firebase_auth
def my_endpoint():
    user = get_current_firebase_user()
    return jsonify({'message': f'Hello {user.email}'})
```

### Frontend: Authentication
```typescript
import { useFirebaseAuth } from '../context/FirebaseAuthContext';

function MyComponent() {
  const { user, loginWithEmail, logout } = useFirebaseAuth();
  
  const handleLogin = async () => {
    try {
      await loginWithEmail('user@example.com', 'password');
    } catch (error) {
      console.error('Login failed:', error.message);
    }
  };
  
  return user ? <div>Welcome {user.email}</div> : <LoginForm />;
}
```

### Frontend: API Calls
```typescript
import axiosInstance from '../services/axiosInstance';

// Axios automatically includes Firebase tokens
const fetchData = async () => {
  try {
    const response = await axiosInstance.get('/api/v1/nextgen/data-sources');
    return response.data;
  } catch (error) {
    if (error.response?.status === 401) {
      // User needs to log in again
    }
    throw error;
  }
};
```

## 🔍 Testing Commands

```bash
# Quick backend test
python test-auth-fixes.py

# Complete system test
python test-e2e-auth.py

# Unit tests
pytest backend/tests/test_firebase_auth.py -v

# Integration tests
pytest backend/tests/test_firebase_integration.py -v
```

## 🚨 Emergency Fixes

### Reset Authentication System
```bash
# 1. Stop services
pkill -f "flask run"
pkill -f "npm run dev"

# 2. Clear browser storage (in browser console)
localStorage.clear();

# 3. Restart services
cd backend && python -m flask run &
cd frontend && npm run dev &

# 4. Test
python test-e2e-auth.py
```

### Force Firebase Reinitialization
```bash
curl -X POST http://localhost:5000/auth/firebase-reinitialize
```

## 📊 Health Check Script

Save as `check-auth-health.sh`:
```bash
#!/bin/bash
echo "🔍 Checking authentication system..."

# Firebase health
FIREBASE_STATUS=$(curl -s http://localhost:5000/auth/firebase-health | jq -r '.status')
echo "Firebase: $FIREBASE_STATUS"

# Configuration
CONFIG_VALID=$(curl -s http://localhost:5000/auth/firebase-config-validation | jq -r '.configuration_valid')
echo "Config: $CONFIG_VALID"

# Protected endpoint (should be 401)
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/nextgen/data-sources)
echo "Auth Required: $AUTH_STATUS"

if [ "$FIREBASE_STATUS" = "healthy" ] && [ "$CONFIG_VALID" = "true" ] && [ "$AUTH_STATUS" = "401" ]; then
    echo "✅ System is healthy"
else
    echo "❌ System has issues"
fi
```

## 📚 Key Files

- **Backend Auth:** `backend/app/middleware/firebase_auth.py`
- **Backend Routes:** `backend/app/routes/firebase_auth_routes.py`
- **Frontend Context:** `frontend/src/context/FirebaseAuthContext.tsx`
- **Frontend Axios:** `frontend/src/services/axiosInstance.ts`
- **Tests:** `test-auth-fixes.py`, `test-e2e-auth.py`
- **Documentation:** `docs/authentication-system.md`
- **Troubleshooting:** `docs/authentication-troubleshooting.md`

## 🔗 Useful URLs

- **Backend Health:** http://localhost:5000/auth/firebase-health
- **Config Validation:** http://localhost:5000/auth/firebase-config-validation
- **Frontend:** http://localhost:5173
- **Firebase Console:** https://console.firebase.google.com/

## 💡 Pro Tips

1. **Always check Firebase health first** when debugging auth issues
2. **Use request IDs** in logs to trace authentication flows
3. **Test with curl** before testing with frontend
4. **Check browser console** for frontend authentication issues
5. **Monitor token expiration** (Firebase tokens expire in 1 hour)
6. **Use the test scripts** to validate your changes

## 🆘 When to Get Help

Contact support if:
- System health checks fail consistently
- Authentication works locally but fails in production
- You see repeated 500 errors in firebase-sync
- Token verification fails with valid tokens
- Database user creation consistently fails

Include debug information from `collect-debug-info.sh` when reporting issues.