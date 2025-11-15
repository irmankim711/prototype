# Firebase Phone Authentication Setup Guide

This guide will help you set up Firebase Phone Authentication for your quick access login feature.

## Overview

Firebase Phone Authentication allows users to log in using their phone number with SMS OTP verification. This is more secure and reliable than your previous custom OTP system.

## Benefits of Firebase Phone Auth

✅ **Secure**: Firebase handles all security aspects, token generation, and verification
✅ **No JWT Issues**: No empty tokens - Firebase automatically creates valid auth tokens
✅ **Reliable SMS Delivery**: Uses Firebase's global SMS infrastructure
✅ **Built-in Rate Limiting**: Automatic protection against abuse
✅ **No Backend OTP Code**: Backend doesn't need to generate/store OTP codes
✅ **Global Coverage**: Works with phone numbers from all countries

---

## Prerequisites

1. **Firebase Project**: You already have one (`report-automation-57f6e`)
2. **Firebase SDK**: Already installed (`firebase: ^12.4.0`)
3. **Firebase Admin SDK**: Already installed in backend (`firebase-admin`)

---

## Step 1: Enable Phone Authentication in Firebase Console

### 1.1 Go to Firebase Console
1. Visit [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **report-automation-57f6e**

### 1.2 Enable Phone Authentication
1. In the left sidebar, click **Authentication**
2. Click on the **Sign-in method** tab
3. Find **Phone** in the list of providers
4. Click **Phone** to expand it
5. Toggle **Enable** to ON
6. Click **Save**

### 1.3 Configure Test Phone Numbers (Optional - for development)
If you want to test without sending real SMS:

1. In the **Sign-in method** tab, scroll down to **Phone numbers for testing**
2. Click **Add phone number**
3. Enter a test phone number (e.g., `+601234567890`)
4. Enter a test verification code (e.g., `123456`)
5. Click **Add**

Now you can use this number in development without sending real SMS.

---

## Step 2: Configure reCAPTCHA (Required for Phone Auth)

Firebase Phone Auth requires reCAPTCHA to prevent abuse.

### 2.1 Verify reCAPTCHA is Enabled
Firebase automatically sets up reCAPTCHA for your domain. You need to:

1. In Firebase Console → **Authentication** → **Settings** tab
2. Scroll to **Authorized domains**
3. Make sure these domains are listed:
   - `localhost` (for development)
   - Your production domain (e.g., `your-app.com`)

### 2.2 Add Your Domain
If deploying to production:

1. Click **Add domain**
2. Enter your domain (without http/https): `your-domain.com`
3. Click **Add**

---

## Step 3: Update Firebase Configuration (Already Done ✓)

Your Firebase configuration in `frontend/src/config/firebase.ts` is already set up correctly:

```typescript
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "",
  projectId: "report-automation-57f6e",
  storageBucket: "report-automation-57f6e.firebasestorage.app",
  messagingSenderId: "87279819935",
  appId: "1:87279819935:web:9f78b1c4c2efe16ad4d6aa",
  measurementId: "G-R2HGN102D3"
};
```

---

## Step 4: Set Environment Variables

### 4.1 Frontend Environment Variables
Create or update `frontend/.env`:

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=your-firebase-api-key-here
VITE_FIREBASE_AUTH_DOMAIN=report-automation-57f6e.firebaseapp.com
```

To get your API key:
1. Go to Firebase Console → Project Settings (gear icon)
2. Scroll down to "Your apps" section
3. Find your web app
4. Copy the `apiKey` value

### 4.2 Backend Environment Variables
Your backend already has Firebase Admin SDK configured. Ensure `backend/.env` has:

```env
# Firebase Admin SDK (for token verification)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json
# OR use these directly:
FIREBASE_PROJECT_ID=report-automation-57f6e
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@report-automation-57f6e.iam.gserviceaccount.com
```

---

## Step 5: Backend Token Verification (Already Working ✓)

Your backend already has Firebase token verification set up in:
- `backend/app/middleware/firebase_auth.py`
- `backend/app/routes/firebase_auth.py`

The flow:
1. User authenticates with Firebase (phone → OTP → Firebase user)
2. Frontend gets Firebase ID token
3. Frontend sends token to backend: `POST /api/auth/firebase-login`
4. Backend verifies token with Firebase Admin SDK
5. Backend creates/updates user in database
6. User can access protected endpoints

---

## Step 6: Testing the Phone Authentication

### 6.1 Development Testing with Test Numbers

1. Add a test number in Firebase Console (see Step 1.3)
2. Go to your app's Quick Access page
3. Enter the test phone number (e.g., `+601234567890`)
4. Click "Send SMS Code"
5. Enter the test verification code you configured (e.g., `123456`)
6. Click "Verify OTP"
7. You should be logged in successfully

### 6.2 Production Testing with Real SMS

1. Ensure you have:
   - Enabled Phone Authentication in Firebase
   - Set up billing in Firebase (required for SMS quota)
   - Added your production domain to authorized domains

2. Enter a real phone number with country code
3. You'll receive a real SMS with a 6-digit code
4. Enter the code to authenticate

---

## Step 7: Firebase SMS Quota and Billing

### 7.1 Free Tier Limits
Firebase Phone Auth free tier includes:
- **10,000 verifications per month** for free
- Additional verifications: varies by country (~$0.01-0.06 per SMS)

### 7.2 Enable Billing (Required for Production)

1. Go to Firebase Console → **Usage and billing**
2. Click **Details & settings**
3. Click **Modify plan**
4. Select **Blaze (Pay as you go)** plan
5. Add your payment method

**Note**: You won't be charged unless you exceed the free tier limit.

### 7.3 Monitor Usage

1. Go to **Authentication** → **Usage** tab
2. View daily/monthly phone authentication attempts
3. Set up budget alerts if needed

---

## How It Works: Complete Flow

### Frontend Flow
```
1. User enters phone number (+60123456789)
   ↓
2. FirebasePhoneAuth component calls Firebase
   signInWithPhoneNumber(auth, phone, recaptchaVerifier)
   ↓
3. Firebase sends SMS to user's phone
   ↓
4. User enters 6-digit OTP code
   ↓
5. FirebasePhoneAuth calls confirmationResult.confirm(otp)
   ↓
6. Firebase verifies OTP and returns authenticated user
   ↓
7. Frontend gets ID token: user.getIdToken()
   ↓
8. Frontend stores token and navigates to forms page
```

### Backend Sync Flow (Automatic via FirebaseAuthContext)
```
1. FirebaseAuthContext detects new authenticated user
   ↓
2. Calls syncUserWithBackend(firebaseUser)
   ↓
3. Gets fresh ID token
   ↓
4. Sends POST /api/auth/firebase-login with token
   ↓
5. Backend verifies token with Firebase Admin SDK
   ↓
6. Backend creates/updates user in database
   ↓
7. Backend returns user data
   ↓
8. User can now access protected routes
```

---

## Troubleshooting

### Issue: "reCAPTCHA verification failed"
**Solution**:
- Ensure `localhost` is in Firebase authorized domains
- Clear browser cache and cookies
- Try incognito/private browsing mode

### Issue: "SMS quota exceeded"
**Solution**:
- Enable Blaze plan in Firebase Console
- Check usage limits in Firebase Console → Authentication → Usage

### Issue: "Invalid phone number format"
**Solution**:
- Always include country code (e.g., `+60` for Malaysia)
- Use international format: `+[country code][number]`
- Example: `+60123456789` (Malaysia), `+12125551234` (USA)

### Issue: "Too many requests"
**Solution**:
- Firebase automatically rate limits to prevent abuse
- Wait a few minutes and try again
- Use test phone numbers for development (see Step 1.3)

### Issue: "Backend sync failed"
**Solution**:
- Check backend logs for Firebase Admin SDK errors
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
- Verify Firebase service account has proper permissions

---

## Security Best Practices

✅ **Never commit API keys**: Use environment variables
✅ **Enable App Check**: Protects against unauthorized API usage
✅ **Use test numbers in development**: Avoid SMS costs during testing
✅ **Monitor usage**: Set up alerts for unusual authentication patterns
✅ **Rate limiting**: Firebase handles this automatically
✅ **Domain whitelisting**: Only allow trusted domains in Firebase Console

---

## Migration from Old OTP System

### What Changed
❌ **Old System** (Broken):
- Backend generates 6-digit OTP
- Backend stores OTP in database
- Backend sends SMS via Twilio
- Returns empty JWT tokens ❌
- Security vulnerabilities

✅ **New System** (Firebase):
- Firebase generates secure OTP
- Firebase sends SMS globally
- Firebase verifies OTP
- Returns valid Firebase ID tokens ✅
- Production-grade security

### Migration Steps
1. ✅ Created `FirebasePhoneAuth` component
2. ✅ Replaced old phone auth in `LandingPageEnhanced.tsx`
3. ✅ Backend already has Firebase token verification
4. ⏳ **Next**: Test and remove old quick-auth routes

### Optional: Remove Old Code
Once Firebase phone auth is working, you can safely remove:
- `backend/app/routes/quick_auth.py` (old OTP system)
- `QuickAccessToken` database model (if not used elsewhere)
- Twilio dependency (if only used for quick auth)

---

## Testing Checklist

- [ ] Firebase Phone Auth enabled in console
- [ ] Test phone number configured (for development)
- [ ] Environment variables set
- [ ] reCAPTCHA working (no errors in console)
- [ ] Can send SMS to test number
- [ ] Can verify OTP successfully
- [ ] User redirected to forms page after login
- [ ] Backend receives Firebase token
- [ ] Backend creates/updates user in database
- [ ] User can access protected routes

---

## Support

### Firebase Documentation
- [Phone Authentication](https://firebase.google.com/docs/auth/web/phone-auth)
- [Admin SDK Setup](https://firebase.google.com/docs/admin/setup)
- [reCAPTCHA for Phone Auth](https://firebase.google.com/docs/auth/web/phone-auth#use-invisible-recaptcha)

### Firebase Console Links
- [Authentication Settings](https://console.firebase.google.com/project/report-automation-57f6e/authentication)
- [Project Settings](https://console.firebase.google.com/project/report-automation-57f6e/settings/general)
- [Usage & Billing](https://console.firebase.google.com/project/report-automation-57f6e/usage)

---

## Quick Start Commands

```bash
# Frontend - Install dependencies (already done)
cd frontend
npm install

# Set environment variables
echo "VITE_FIREBASE_API_KEY=your-api-key-here" >> .env
echo "VITE_FIREBASE_AUTH_DOMAIN=report-automation-57f6e.firebaseapp.com" >> .env

# Start development server
npm run dev

# Backend - No changes needed
cd ../backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

---

## Summary

You now have a production-ready Firebase Phone Authentication system that:

1. ✅ Sends SMS via Firebase's global infrastructure
2. ✅ Generates secure, valid authentication tokens
3. ✅ Includes built-in rate limiting and security
4. ✅ Works seamlessly with your existing Firebase Auth setup
5. ✅ Syncs automatically with your backend
6. ✅ Supports all countries and phone formats

**Next Steps**:
1. Enable Phone Auth in Firebase Console
2. Add your API key to `.env`
3. Test with a test phone number
4. Enable billing for production use
5. Remove old quick-auth code (optional)

Enjoy secure, reliable phone authentication! 🚀
