# Firebase Auth - Quick Reference Card

## 🚀 Quick Start

### Installation
```bash
npm install firebase@12.4.0
```

### Basic Setup
```typescript
import { initializeApp } from 'firebase/app';
import { getAuth, setPersistence, browserLocalPersistence } from 'firebase/auth';

const app = initializeApp({ /* config */ });
const auth = getAuth(app);

// Set persistence explicitly
setPersistence(auth, browserLocalPersistence);
```

---

## 🔑 Common Patterns

### Email/Password Login (Fixed Version)
```typescript
const loginWithEmail = async (email: string, password: string) => {
  setIsLoading(true);

  const { signInWithEmailAndPassword } = await import('firebase/auth');
  const userCredential = await signInWithEmailAndPassword(auth, email, password);

  // ✅ CRITICAL: Immediately update state
  setFirebaseUser(userCredential.user);
  setUser(convertUser(userCredential.user));

  // Store token
  const token = await userCredential.user.getIdToken(true);
  localStorage.setItem('firebaseToken', token);

  setIsLoading(false);
};
```

### Google OAuth Login (Fixed Version)
```typescript
const loginWithGoogle = async () => {
  setIsLoading(true);

  const { signInWithPopup } = await import('firebase/auth');
  const result = await signInWithPopup(auth, googleProvider);

  // ✅ CRITICAL: Immediately update state
  setFirebaseUser(result.user);
  setUser(convertUser(result.user));

  // Store token
  const token = await result.user.getIdToken(true);
  localStorage.setItem('firebaseToken', token);

  setIsLoading(false);
};
```

### Logout (Fixed Version)
```typescript
const logout = async () => {
  const { signOut } = await import('firebase/auth');
  await signOut(auth);

  // ✅ CRITICAL: Clear ALL Firebase keys from localStorage
  const firebaseKeys: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith('firebase:')) {
      firebaseKeys.push(key);
    }
  }

  firebaseKeys.forEach(key => localStorage.removeItem(key));
  localStorage.removeItem('firebaseToken');

  // Clear state
  setFirebaseUser(null);
  setUser(null);
};
```

### Auth State Listener
```typescript
useEffect(() => {
  const { onAuthStateChanged } = await import('firebase/auth');

  const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
    if (firebaseUser) {
      setFirebaseUser(firebaseUser);
      setUser(convertUser(firebaseUser));

      // Refresh token
      const token = await firebaseUser.getIdToken();
      localStorage.setItem('firebaseToken', token);
    } else {
      setFirebaseUser(null);
      setUser(null);
      localStorage.removeItem('firebaseToken');
    }

    setIsLoading(false);
  });

  return () => unsubscribe();
}, []);
```

### Token Refresh
```typescript
useEffect(() => {
  if (!firebaseUser) return;

  const refreshToken = async () => {
    const token = await firebaseUser.getIdToken(true); // Force refresh
    localStorage.setItem('firebaseToken', token);
  };

  // Refresh every 50 minutes (tokens expire in 60 minutes)
  const interval = setInterval(refreshToken, 50 * 60 * 1000);
  refreshToken(); // Initial refresh

  return () => clearInterval(interval);
}, [firebaseUser]);
```

---

## 🐛 Debugging Commands

### Browser Console
```javascript
// Inspect current auth state
window.authDebug.inspectAuth()

// Check all localStorage keys
window.authDebug.inspectStorage()

// Clear Firebase keys manually
window.authDebug.clearFirebaseKeys()

// Monitor auth changes in real-time
const stop = window.authDebug.monitorAuthChanges()
// ... perform actions ...
stop()

// Test logout cleanup
window.authDebug.testLogoutCleanup()
```

### Check Token Expiration
```javascript
const token = localStorage.getItem('firebaseToken');
if (token) {
  const payload = JSON.parse(atob(token.split('.')[1]));
  const exp = new Date(payload.exp * 1000);
  console.log('Token expires:', exp.toISOString());
  console.log('Is expired:', Date.now() > payload.exp * 1000);
}
```

### Check Firebase Keys
```javascript
Object.keys(localStorage)
  .filter(k => k.startsWith('firebase:'))
  .forEach(k => console.log(k, localStorage.getItem(k)?.substring(0, 50)));
```

---

## ⚠️ Common Pitfalls

### ❌ DON'T: Wait for onAuthStateChanged
```typescript
// BAD: UI won't update until listener fires (2-5 second delay)
await signInWithEmailAndPassword(auth, email, password);
// No state update here!
```

### ✅ DO: Update state immediately
```typescript
// GOOD: UI updates instantly
const userCredential = await signInWithEmailAndPassword(auth, email, password);
setFirebaseUser(userCredential.user); // Immediate update
```

---

### ❌ DON'T: Only remove custom keys on logout
```typescript
// BAD: Firebase keys remain in localStorage!
localStorage.removeItem('firebaseToken');
// firebase:authUser:* keys still exist!
```

### ✅ DO: Clear ALL Firebase keys
```typescript
// GOOD: Complete cleanup
for (let i = 0; i < localStorage.length; i++) {
  const key = localStorage.key(i);
  if (key?.startsWith('firebase:')) {
    localStorage.removeItem(key);
  }
}
localStorage.removeItem('firebaseToken');
```

---

### ❌ DON'T: Block UI during backend sync
```typescript
// BAD: UI frozen until sync completes
const backendUser = await syncWithBackend(firebaseUser);
setUser(backendUser);
```

### ✅ DO: Run backend sync in background
```typescript
// GOOD: UI updates immediately, sync in background
setFirebaseUser(firebaseUser);

syncWithBackend(firebaseUser)
  .then(setUser)
  .catch(err => {
    // Use fallback user for offline operation
    setUser(createFallbackUser(firebaseUser));
  });
```

---

## 📊 Persistence Modes

```typescript
import {
  browserLocalPersistence,   // Survives browser close
  browserSessionPersistence, // Cleared when tab closes
  inMemoryPersistence       // Cleared on page reload
} from 'firebase/auth';

// Set persistence
await setPersistence(auth, browserLocalPersistence);
```

| Mode | Survives Reload | Survives Browser Close | Use Case |
|------|-----------------|------------------------|----------|
| `browserLocalPersistence` | ✅ | ✅ | Normal apps (default) |
| `browserSessionPersistence` | ✅ | ❌ | Shared computers |
| `inMemoryPersistence` | ❌ | ❌ | High security |

---

## 🔐 Security Checklist

- [ ] Use HTTPS in production
- [ ] Enable Firebase App Check
- [ ] Implement rate limiting
- [ ] Clear ALL Firebase keys on logout
- [ ] Validate tokens on backend
- [ ] Use Firebase Security Rules
- [ ] Monitor auth events
- [ ] Set appropriate token expiration
- [ ] Implement CSRF protection
- [ ] Use secure cookie settings

---

## 📞 Error Codes

| Code | Meaning | User Message |
|------|---------|--------------|
| `auth/user-not-found` | Email not registered | "No account found with this email" |
| `auth/wrong-password` | Incorrect password | "Incorrect password" |
| `auth/invalid-email` | Malformed email | "Invalid email address" |
| `auth/too-many-requests` | Rate limited | "Too many attempts. Try again later" |
| `auth/network-request-failed` | Network error | "Network error. Check connection" |
| `auth/popup-closed-by-user` | OAuth cancelled | "Login cancelled" |
| `auth/popup-blocked` | Popup blocked | "Please allow popups" |

---

## 🎯 Key Fixes Applied

### Fix #1: Token Persistence After Logout
**Problem:** Firebase keys remain in localStorage after logout
**Solution:** Iterate and remove ALL keys starting with `firebase:`

### Fix #2: Delayed UI Update After Login
**Problem:** UI shows logged out until page reload
**Solution:** Immediately call `setFirebaseUser()` after successful auth

---

## 📚 Resources

- [Full Guide](./FIREBASE_AUTH_FIX_GUIDE.md)
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- [Reference Implementation](./frontend/src/context/AuthProvider.example.tsx)
- [Debug Tools](./frontend/src/utils/authDebugger.ts)

---

## 🆘 Quick Troubleshooting

### UI doesn't update after login
```typescript
// Check: Are you updating state immediately?
const userCredential = await signInWithEmailAndPassword(...);
setFirebaseUser(userCredential.user); // ← Must be here!
```

### Token persists after logout
```javascript
// Check: Are you clearing Firebase keys?
window.authDebug.inspectStorage()
// Should show NO firebase:* keys after logout
```

### Token expired errors
```typescript
// Check: Is token refresh working?
// Should refresh every 50 minutes automatically
useEffect(() => {
  if (!firebaseUser) return;
  const interval = setInterval(() => {
    firebaseUser.getIdToken(true).then(token => {
      localStorage.setItem('firebaseToken', token);
    });
  }, 50 * 60 * 1000);
  return () => clearInterval(interval);
}, [firebaseUser]);
```

---

**Last Updated:** 2025-01-04
**Firebase SDK:** v12.4.0
**Status:** ✅ Production Ready
