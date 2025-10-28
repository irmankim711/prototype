# Quick Setup Guide: Rate Limiting & Security Features

This guide will help you integrate the new rate limiting and security features into your login components.

## Step 1: Install Dependencies

All dependencies are already included. No additional installation needed.

## Step 2: Update Your Login Component

Here's a complete example of how to integrate rate limiting into your login component:

```typescript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFirebaseAuth } from '@/context/FirebaseAuthContext';
import { useLoginRateLimit } from '@/hooks/useLoginRateLimit';
import { RateLimitAlert } from '@/components/Auth/RateLimitAlert';

export function LoginPage() {
  const navigate = useNavigate();
  const { loginWithEmail, loginWithGoogle } = useFirebaseAuth();

  // Rate limiting hook
  const {
    canAttemptLogin,
    remainingAttempts,
    lockoutTimeRemaining,
    recordAttempt,
    getErrorMessage,
  } = useLoginRateLimit();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Check rate limit before attempting login
    if (!canAttemptLogin) {
      setError(getErrorMessage());
      return;
    }

    setIsLoading(true);

    try {
      await loginWithEmail(email, password);
      recordAttempt(true); // Success - reset counter
      navigate('/dashboard');
    } catch (err: any) {
      recordAttempt(false); // Failure - increment counter
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    setIsLoading(true);

    try {
      await loginWithGoogle();
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = () => {
    navigate('/reset-password');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        <h2 className="text-3xl font-bold text-center">Sign In</h2>

        {/* Rate Limit Alert */}
        <RateLimitAlert
          isLocked={!canAttemptLogin}
          lockoutTimeRemaining={lockoutTimeRemaining}
          remainingAttempts={remainingAttempts}
          warningMessage={getErrorMessage()}
          onResetPassword={handleResetPassword}
          onGoogleSignIn={handleGoogleLogin}
          className="mb-4"
        />

        {/* General Error Message */}
        {error && !getErrorMessage() && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Email/Password Form */}
        <form onSubmit={handleEmailLogin} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={!canAttemptLogin}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={!canAttemptLogin}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={handleResetPassword}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              Forgot password?
            </button>

            {remainingAttempts <= 2 && remainingAttempts > 0 && (
              <span className="text-sm text-yellow-600">
                {remainingAttempts} attempt{remainingAttempts === 1 ? '' : 's'} remaining
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading || !canAttemptLogin}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-gray-50 text-gray-500">Or continue with</span>
          </div>
        </div>

        {/* Google Sign-In */}
        <button
          onClick={handleGoogleLogin}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
```

## Step 3: Enable Firebase App Check (Production Only)

### Get reCAPTCHA Site Key

1. Visit [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Click "+" to create a new site
3. Choose **reCAPTCHA v3**
4. Add your domains
5. Copy the **Site Key**

### Configure in Firebase

1. Go to [Firebase Console - App Check](https://console.firebase.google.com/project/report-automation-57f6e/appcheck)
2. Click "Get Started"
3. Register your web app
4. Select "reCAPTCHA v3"
5. Paste your site key

### Update Environment Variables

Add to your `.env` file:

```bash
VITE_RECAPTCHA_SITE_KEY=your_actual_recaptcha_site_key
VITE_APP_CHECK_ENABLED=true
```

## Step 4: Test the Implementation

### Manual Testing Checklist

- [ ] Try logging in with correct credentials → Should work
- [ ] Try logging in with wrong password 4 times → Should show warning
- [ ] Try 5th wrong attempt → Should show lockout with countdown
- [ ] Wait for lockout to expire → Should allow login again
- [ ] Click "Forgot Password" during lockout → Should navigate to reset page
- [ ] Try Google Sign-In during lockout → Should work (bypasses email lockout)

### Automated Testing

```typescript
// Example test
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginPage } from './LoginPage';

describe('Login Rate Limiting', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should lock out after 5 failed attempts', async () => {
    const { container } = render(<LoginPage />);

    // Attempt 5 failed logins
    for (let i = 0; i < 5; i++) {
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'wrong_password' },
      });
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
      await waitFor(() => {});
    }

    // Should show lockout message
    expect(screen.getByText(/temporarily locked/i)).toBeInTheDocument();

    // Submit button should be disabled
    expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled();
  });
});
```

## Step 5: Monitor Security Events

### View in Development

Open browser console:

```javascript
// View recent security events
import { securityMonitoring } from './services/securityMonitoring';
console.table(securityMonitoring.getRecentEvents(20));

// View statistics
console.log(securityMonitoring.getStatistics());
```

### Set Up Production Monitoring (Optional)

Integrate with your monitoring service in `frontend/src/services/securityMonitoring.ts`:

```typescript
// Example: Send to your backend
private sendToMonitoringService(event: SecurityEvent): void {
  fetch('/api/security/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
  }).catch(console.error);
}
```

## Troubleshooting

### Issue: Rate limit not working

**Check:**
```javascript
// In browser console
console.log(localStorage.getItem('login_rate_limit'));
```

**Solution:** Clear localStorage and refresh:
```javascript
localStorage.removeItem('login_rate_limit');
location.reload();
```

### Issue: Firebase rate limit triggered immediately

**Cause:** Previous failed attempts within last 15-30 minutes

**Solutions:**
1. Wait 30 minutes
2. Use "Forgot Password" to reset
3. Try Google Sign-In instead

### Issue: App Check blocking requests

**Check:**
```javascript
import { getAppCheckToken } from './config/firebaseAppCheck';
getAppCheckToken().then(console.log);
```

**Solutions:**
1. Verify `VITE_RECAPTCHA_SITE_KEY` is correct
2. Check domain is whitelisted in reCAPTCHA settings
3. Use debug token in development

## What You've Implemented

✅ **Client-side rate limiting** - Prevents excessive login attempts before hitting Firebase limits

✅ **Enhanced error messages** - User-friendly messages with recovery instructions

✅ **Rate limit UI components** - Visual feedback with countdown timers

✅ **Security monitoring** - Comprehensive logging of authentication events

✅ **Firebase App Check** - Production-ready bot protection

✅ **No automatic retries** - Prevents accidental rate limit triggers

✅ **Password reset integration** - Easy recovery path for locked users

✅ **Google Sign-In fallback** - Alternative authentication during lockouts

## Next Steps

1. Test thoroughly in development
2. Set up reCAPTCHA for production
3. Enable App Check in Firebase Console
4. Integrate security monitoring with your analytics
5. Train support team on handling locked-out users
6. Monitor rate limit events in production

## Questions?

Refer to the comprehensive [Authentication Rate Limiting Guide](./AUTHENTICATION_RATE_LIMITING.md) for detailed information.
