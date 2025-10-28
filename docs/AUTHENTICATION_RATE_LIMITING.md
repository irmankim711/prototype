# Authentication Rate Limiting & Security Guide

## Overview

This document explains how authentication rate limiting works in our application and how to handle Firebase's `auth/too-many-requests` error.

## Table of Contents

1. [Understanding Rate Limiting](#understanding-rate-limiting)
2. [Client-Side Protection](#client-side-protection)
3. [Firebase Rate Limiting](#firebase-rate-limiting)
4. [Implementation Details](#implementation-details)
5. [User Experience](#user-experience)
6. [Security Monitoring](#security-monitoring)
7. [Firebase App Check](#firebase-app-check)
8. [Troubleshooting](#troubleshooting)

---

## Understanding Rate Limiting

### What is Rate Limiting?

Rate limiting is a security mechanism that restricts the number of authentication attempts a user can make within a specific time period. This protects against:

- **Brute-force attacks**: Automated attempts to guess passwords
- **Credential stuffing**: Using stolen credentials from data breaches
- **Account enumeration**: Discovering which email addresses have accounts

### Two Layers of Protection

Our application implements **two layers** of rate limiting:

1. **Client-Side Rate Limiting** (First line of defense)
   - Limits: 5 attempts per 15-minute window
   - Lockout: 5 minutes after max attempts
   - Purpose: Provide immediate feedback and reduce unnecessary API calls

2. **Firebase Server-Side Rate Limiting** (Backend protection)
   - Limits: ~5-10 attempts (Firebase-managed, not publicly documented)
   - Lockout: 15 minutes to several hours depending on severity
   - Purpose: Prevent abuse even if client-side checks are bypassed

---

## Client-Side Protection

### Using the Rate Limiting Hook

```typescript
import { useLoginRateLimit } from '@/hooks/useLoginRateLimit';

function LoginForm() {
  const {
    canAttemptLogin,
    remainingAttempts,
    lockoutTimeRemaining,
    recordAttempt,
    reset,
    getErrorMessage,
  } = useLoginRateLimit();

  const handleLogin = async (email: string, password: string) => {
    // Check if user is locked out
    if (!canAttemptLogin) {
      setError(getErrorMessage());
      return;
    }

    try {
      await loginWithEmail(email, password);
      recordAttempt(true); // Success - reset counter
    } catch (error) {
      recordAttempt(false); // Failure - increment counter
      setError(error.message);
    }
  };

  // ... rest of component
}
```

### Hook API Reference

| Property | Type | Description |
|----------|------|-------------|
| `canAttemptLogin` | `boolean` | Whether the user can attempt to login |
| `remainingAttempts` | `number` | Number of attempts left before lockout |
| `lockoutTimeRemaining` | `number` | Seconds remaining in lockout period |
| `recordAttempt(success)` | `function` | Record a login attempt (pass `true` for success, `false` for failure) |
| `reset()` | `function` | Manually reset the rate limit state |
| `getErrorMessage()` | `function` | Get user-friendly error message |

---

## Firebase Rate Limiting

### Understanding `auth/too-many-requests`

When Firebase returns this error:

```
FirebaseError: Firebase: Error (auth/too-many-requests)
```

**What it means:**
- The account has had too many failed login attempts
- Firebase has **temporarily blocked** authentication for this account
- This is a security feature, not a bug

**Typical causes:**
- Multiple failed password attempts
- Automated testing without proper cleanup
- Multiple browser tabs attempting to login
- Retry logic creating loops

**Lockout duration:**
- Initial lockout: **15-30 minutes**
- Repeated violations: **Up to several hours**
- The exact duration is managed by Firebase and not publicly documented

### Error Response Format

```javascript
{
  code: "auth/too-many-requests",
  message: "Firebase: Error (auth/too-many-requests)."
}
```

Our application transforms this into:

```
"Too many failed login attempts. This account is temporarily locked for security.
Please wait 15-30 minutes and try again, or reset your password using the 'Forgot Password' link.
You can also try signing in with Google if available."
```

---

## Implementation Details

### File Structure

```
frontend/src/
├── hooks/
│   └── useLoginRateLimit.ts          # Client-side rate limiting hook
├── services/
│   └── securityMonitoring.ts         # Security event logging
├── components/
│   └── Auth/
│       └── RateLimitAlert.tsx        # UI component for rate limit messages
├── config/
│   ├── firebase.ts                   # Firebase initialization
│   └── firebaseAppCheck.ts           # App Check configuration
└── context/
    └── FirebaseAuthContext.tsx       # Auth context with integrated monitoring
```

### Rate Limit Storage

Client-side rate limiting state is stored in `localStorage`:

```javascript
{
  attempts: 3,                    // Number of failed attempts
  lastAttemptTime: 1698765432000, // Timestamp of last attempt
  isLocked: false,                // Whether user is locked out
  lockoutEndsAt: null             // When lockout expires
}
```

**Key:** `login_rate_limit`

---

## User Experience

### UI Components

#### RateLimitAlert Component

Displays contextual alerts based on rate limit state:

```tsx
import { RateLimitAlert } from '@/components/Auth/RateLimitAlert';

<RateLimitAlert
  isLocked={!canAttemptLogin}
  lockoutTimeRemaining={lockoutTimeRemaining}
  remainingAttempts={remainingAttempts}
  warningMessage={getErrorMessage()}
  onResetPassword={() => navigate('/reset-password')}
  onGoogleSignIn={() => loginWithGoogle()}
/>
```

**States:**

1. **Normal** (5-3 attempts remaining): No alert shown
2. **Warning** (2-1 attempts remaining): Yellow warning banner
3. **Locked** (0 attempts): Red error banner with countdown timer

#### Example User Flow

```
Attempt 1: ❌ Wrong password → "Incorrect password"
Attempt 2: ❌ Wrong password → "Incorrect password"
Attempt 3: ❌ Wrong password → "Incorrect password"
Attempt 4: ⚠️  Wrong password → "Warning: 1 attempt remaining before temporary lockout"
Attempt 5: 🔒 Account locked → "Too many failed attempts. Please wait 5 minutes..."
           (Countdown timer shows: 4:59, 4:58, 4:57...)
After 5 min: ✅ Unlocked → User can try again
```

---

## Security Monitoring

### Event Logging

All security events are logged via `securityMonitoring` service:

```typescript
import { securityMonitoring } from '@/services/securityMonitoring';

// Automatic logging in FirebaseAuthContext
securityMonitoring.logFirebaseRateLimit(email);
securityMonitoring.logLoginFailure(errorCode, errorMessage, email);
```

### Event Types

| Event Type | Severity | Description |
|------------|----------|-------------|
| `rate_limit_triggered` | High/Critical | Client or Firebase rate limit activated |
| `rate_limit_warning` | Medium | User approaching rate limit |
| `login_failure` | Varies | Failed login attempt |
| `suspicious_activity` | High | Unusual authentication patterns |

### Viewing Security Logs

In development console:

```javascript
// Get recent security events
console.log(securityMonitoring.getRecentEvents(50));

// Get statistics
console.log(securityMonitoring.getStatistics());

// Export for analysis
console.log(securityMonitoring.exportEvents());
```

### Production Integration

For production, integrate with monitoring services:

```typescript
// In securityMonitoring.ts

// Sentry
if (window.Sentry) {
  window.Sentry.captureMessage(event.message, {
    level: event.severity,
    extra: event.metadata,
  });
}

// LogRocket
if (window.LogRocket) {
  window.LogRocket.track(event.type, event.metadata);
}

// Custom backend
fetch('/api/security/events', {
  method: 'POST',
  body: JSON.stringify(event),
});
```

---

## Firebase App Check

### What is App Check?

Firebase App Check protects your backend resources from abuse by verifying that requests come from your authentic app. It uses:

- **reCAPTCHA v3** (Web)
- **DeviceCheck** (iOS)
- **Play Integrity** (Android)

### Setup Instructions

#### Step 1: Enable App Check in Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/project/report-automation-57f6e/appcheck)
2. Click "Get Started"
3. Register your web app
4. Select **reCAPTCHA v3** as the provider

#### Step 2: Get reCAPTCHA Site Key

1. Go to [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Click "+" to create a new site
3. Select **reCAPTCHA v3**
4. Add your domains (including localhost for development)
5. Copy the **Site Key**

#### Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# Production
VITE_RECAPTCHA_SITE_KEY=your_recaptcha_v3_site_key_here
VITE_APP_CHECK_ENABLED=true

# Development (optional debug token)
VITE_APP_CHECK_DEBUG_TOKEN=your_debug_token_from_firebase_console
```

#### Step 4: Enable in Firebase Console

1. In App Check settings, enable enforcement for:
   - **Authentication**
   - **Firestore** (if used)
   - **Cloud Storage** (if used)

### Testing App Check

#### Development Mode

```bash
# In Firebase Console, generate a debug token
# Add to .env
VITE_APP_CHECK_DEBUG_TOKEN=ABCDEF12-3456-7890-ABCD-EF1234567890

# App Check will use debug token instead of reCAPTCHA
```

#### Production Mode

App Check runs automatically when `VITE_RECAPTCHA_SITE_KEY` is set.

---

## Troubleshooting

### Common Issues

#### Issue 1: "Too many requests" immediately after deployment

**Cause:** Previous failed attempts still in Firebase's memory

**Solutions:**
1. Wait 30 minutes for automatic reset
2. Use "Forgot Password" to reset credentials
3. Try Google Sign-In instead
4. In Firebase Console: Delete and recreate user (last resort)

---

#### Issue 2: Client-side lockout won't clear

**Cause:** localStorage not clearing properly

**Solutions:**
```javascript
// Manually clear in browser console
localStorage.removeItem('login_rate_limit');

// Or reset programmatically
import { useLoginRateLimit } from '@/hooks/useLoginRateLimit';
const { reset } = useLoginRateLimit();
reset();
```

---

#### Issue 3: Rate limiting too aggressive during development

**Cause:** Automated tests or hot-reload triggering multiple attempts

**Solutions:**
1. Use development bypass mode (if enabled)
2. Clear rate limit state between tests
3. Use Google Sign-In for testing
4. Mock Firebase auth in tests

```typescript
// In test setup
beforeEach(() => {
  localStorage.removeItem('login_rate_limit');
});
```

---

#### Issue 4: App Check blocking legitimate requests

**Cause:** reCAPTCHA failing or not configured correctly

**Solutions:**
1. Check browser console for App Check errors
2. Verify reCAPTCHA site key is correct
3. Ensure domain is whitelisted in reCAPTCHA settings
4. Use debug token in development
5. Check Firebase Console > App Check for token metrics

---

### Debug Commands

```javascript
// Check current rate limit state
console.log(JSON.parse(localStorage.getItem('login_rate_limit')));

// Check security events
import { securityMonitoring } from '@/services/securityMonitoring';
console.log(securityMonitoring.getStatistics());

// Check App Check token
import { getAppCheckToken } from '@/config/firebaseAppCheck';
getAppCheckToken().then(console.log);

// Check Firebase auth state
import { auth } from '@/config/firebase';
console.log(auth.currentUser);
```

---

## Best Practices

### For Users

1. **Use a password manager** to avoid typos
2. **Reset password** if locked out (faster than waiting)
3. **Try Google Sign-In** as alternative
4. **Don't spam login button** - each attempt counts
5. **Close duplicate tabs** that might be auto-retrying

### For Developers

1. **Never bypass rate limiting** in production
2. **Test with valid credentials** in development
3. **Clear auth state** between test runs
4. **Monitor security events** regularly
5. **Use App Check** in production
6. **Implement proper error handling** for all auth errors
7. **Don't log sensitive data** (passwords, tokens)
8. **Use debug tokens** for App Check in development

### For Operations

1. **Monitor rate limit events** in production
2. **Set up alerts** for excessive rate limiting
3. **Review security logs** weekly
4. **Keep Firebase SDK updated**
5. **Test App Check** before deploying
6. **Have a runbook** for locked-out users

---

## Additional Resources

- [Firebase Authentication Errors](https://firebase.google.com/docs/reference/js/auth#autherrorcodes)
- [Firebase App Check Documentation](https://firebase.google.com/docs/app-check)
- [reCAPTCHA v3 Documentation](https://developers.google.com/recaptcha/docs/v3)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

## Support

If you encounter issues not covered in this guide:

1. Check browser console for detailed error messages
2. Review security monitoring logs
3. Check Firebase Console for service status
4. Contact the development team with:
   - Error message and code
   - Steps to reproduce
   - Browser and OS information
   - Security event logs (if available)
