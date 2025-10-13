# Firebase OAuth Migration Guide

## Overview
This guide covers migrating from the existing JWT-based authentication system to Firebase OAuth. The implementation supports both authentication methods during the transition period.

## 🚀 Quick Start

### 1. Environment Variables
Add these to your `.env` files:

```env
# Firebase Configuration (Frontend)
VITE_FIREBASE_API_KEY=AIzaSyCGpr8w2sPsngexBYBg6ktNE64IWENtD2Q
VITE_FIREBASE_AUTH_DOMAIN=report-automation-57f6e.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=report-automation-57f6e
VITE_FIREBASE_STORAGE_BUCKET=report-automation-57f6e.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=87279819935
VITE_FIREBASE_APP_ID=1:87279819935:web:9f78b1c4c2efe16ad4d6aa
VITE_FIREBASE_MEASUREMENT_ID=G-R2HGN102D3

# Firebase Configuration (Backend)
FIREBASE_PROJECT_ID=report-automation-57f6e
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccountKey.json
# OR use environment variables:
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_private_key\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@report-automation-57f6e.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_CERT_URL=your_cert_url

# Optional: Firebase Emulator (Development)
VITE_FIREBASE_USE_EMULATOR=true
```

### 2. Firebase Console Setup
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: `report-automation-57f6e`
3. Enable Authentication:
   - Go to Authentication > Sign-in method
   - Enable Email/Password and Google providers
4. Generate Service Account Key:
   - Go to Project Settings > Service accounts
   - Generate new private key
   - Download JSON file and set `FIREBASE_SERVICE_ACCOUNT_PATH`

### 3. Database Migration
Run this SQL to add Firebase UID column:

```sql
ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(255) UNIQUE;
CREATE INDEX idx_user_firebase_uid ON user(firebase_uid);
```

## 📁 New Files Created

### Frontend Files
- `frontend/src/config/firebase.ts` - Firebase configuration
- `frontend/src/context/FirebaseAuthContext.tsx` - Firebase auth context
- `frontend/src/components/FirebaseLoginForm.tsx` - Login component
- `frontend/src/components/FirebaseRegisterForm.tsx` - Registration component

### Backend Files
- `backend/app/middleware/firebase_auth.py` - Firebase token verification
- `backend/app/routes/firebase_auth_routes.py` - Firebase auth endpoints

## 🔄 Migration Strategy

### Phase 1: Dual Authentication (Current)
Both JWT and Firebase auth work side by side:

**Frontend Usage:**
```typescript
// Option 1: Use Firebase Auth
import { useFirebaseAuth } from '../context/FirebaseAuthContext';
const { loginWithEmail, loginWithGoogle } = useFirebaseAuth();

// Option 2: Keep using existing JWT auth
import { useAuth } from '../context/AuthContext';
const { login } = useAuth();
```

**Backend Usage:**
```python
# Option 1: Firebase auth decorator
from app.middleware.firebase_auth import require_firebase_auth

@app.route('/protected')
@require_firebase_auth
def protected_route():
    user = get_current_firebase_user()
    return jsonify({'user': user.to_dict()})

# Option 2: Existing JWT auth
from flask_jwt_extended import jwt_required

@app.route('/protected-jwt')
@jwt_required()
def protected_jwt_route():
    # Existing JWT implementation
```

### Phase 2: Firebase Primary (Future)
1. Update all components to use Firebase auth
2. Migrate existing users to Firebase
3. Keep JWT for API keys only

### Phase 3: Firebase Only (Future)
1. Remove JWT authentication completely
2. Update all routes to use Firebase auth
3. Clean up old authentication code

## 🔧 Component Updates

### Replace Login Form
```tsx
// Old
import { LoginForm } from '../components/LoginForm';
<LoginForm />

// New
import { FirebaseLoginForm } from '../components/FirebaseLoginForm';
<FirebaseLoginForm 
  onSuccess={() => navigate('/dashboard')}
  onRegisterClick={() => setShowRegister(true)}
/>
```

### Replace Auth Context
```tsx
// Old
import { AuthProvider, useAuth } from '../context/AuthContext';

// New
import { FirebaseAuthProvider, useFirebaseAuth } from '../context/FirebaseAuthContext';

function App() {
  return (
    <FirebaseAuthProvider>
      <Router>
        {/* Your app content */}
      </Router>
    </FirebaseAuthProvider>
  );
}
```

### Update API Calls
The Firebase context automatically handles token management. No changes needed for API calls - tokens are automatically included in requests.

## 🛡️ Security Features

### Firebase Auth Benefits
- **Built-in Security**: Google handles token validation and refresh
- **Multiple Providers**: Email/password, Google, Facebook, etc.
- **Rate Limiting**: Built-in protection against brute force
- **User Management**: Firebase console for user administration
- **Mobile Ready**: Native SDKs available

### Backend Security
- Token verification through Firebase Admin SDK
- Automatic user creation and linking
- Role-based access control maintained
- Session tracking preserved

## 🧪 Testing

### Development Testing
1. Start with development bypass (existing):
```typescript
const { enableDevelopmentBypass } = useFirebaseAuth();
enableDevelopmentBypass(); // Creates mock admin user
```

2. Test Firebase auth:
```typescript
// Email/password
await loginWithEmail('test@example.com', 'password123');

// Google OAuth
await loginWithGoogle();
```

### Backend Endpoints
Test Firebase auth endpoints:

```bash
# Health check
curl http://localhost:5000/api/firebase-auth/firebase-health

# Verify token
curl -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     http://localhost:5000/api/firebase-auth/verify-token

# Get profile
curl -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     http://localhost:5000/api/firebase-auth/profile
```

## 📊 User Data Migration

### Existing Users
Users with existing accounts will be automatically linked when they first log in with Firebase using the same email address.

### New Users
New users registering through Firebase will be created in the database with:
- Firebase UID for authentication
- Email from Firebase
- Role set to USER (default)
- All profile fields available for updating

## 🐛 Troubleshooting

### Common Issues

**1. "Firebase not initialized"**
- Check service account key path
- Verify environment variables
- Ensure Firebase project ID matches

**2. "Token verification failed"**
- Check Firebase token in network tab
- Verify clock synchronization
- Ensure token hasn't expired

**3. "User creation failed"**
- Check database connection
- Verify user table schema
- Check for email uniqueness conflicts

**4. CORS issues**
- Add your domain to Firebase Auth authorized domains
- Check CORS configuration in backend
- Verify allowed origins

### Debug Mode
Enable debug logging:

```python
import logging
logging.getLogger('app.middleware.firebase_auth').setLevel(logging.DEBUG)
```

## 🔄 Rollback Plan

If issues occur, you can quickly rollback:

1. **Frontend**: Switch back to original AuthContext
2. **Backend**: Remove Firebase auth decorators
3. **Database**: Firebase UID column is optional and won't break existing functionality

## 📈 Monitoring

Monitor Firebase auth through:
- Firebase Console Analytics
- Backend logs for token verification
- User creation/login events
- Error tracking (existing Sentry integration)

## 🎯 Next Steps

1. **Test** the Firebase implementation in development
2. **Configure** Firebase Console settings
3. **Deploy** to staging for further testing
4. **Plan** user migration timeline
5. **Update** frontend components gradually
6. **Monitor** performance and user experience

## 📞 Support

For issues with this migration:
1. Check Firebase Console for auth errors
2. Review backend logs for token verification
3. Test with development bypass mode
4. Verify environment variables are set correctly

The dual auth system ensures a smooth transition with minimal disruption to existing users.