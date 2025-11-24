# URGENT: Railway Production Environment Variable Fix

## Problem

Production is still showing the old Google Client ID (`1008582896300-sbsrcs6jg32lncrnmmf1ia93vnl81tls`) even though all source code has been updated.

**Root Cause**: Railway uses the `.env.production` file during build, which still had the old client ID. However, this file is in `.gitignore` and cannot be committed to git.

## Solution

You must update the environment variable **directly in Railway Dashboard**.

---

## Step-by-Step Fix (URGENT)

### 1. Go to Railway Dashboard

URL: https://railway.app/

### 2. Select Your Frontend Service

- Navigate to your project
- Click on the **frontend** service (not backend)

### 3. Go to Variables Tab

- Click on **Variables** in the left sidebar
- You'll see a list of environment variables

### 4. Update Google Client ID

Find the variable:
```
VITE_GOOGLE_CLIENT_ID
```

**Current (WRONG) value:**
```
1008582896300-sbsrcs6jg32lncrnmmf1ia93vnl81tls.apps.googleusercontent.com
```

**New (CORRECT) value:**
```
87279819935-i7a1r6kruor58op1jom3mhgcvkvpc7uh.apps.googleusercontent.com
```

Steps:
1. Click on `VITE_GOOGLE_CLIENT_ID` to edit it
2. Replace the value with the new client ID above
3. Click **Save** or **Update**

### 5. Trigger Redeploy

Railway should automatically redeploy when you change environment variables. If not:

1. Go to **Deployments** tab
2. Click **Redeploy** on the latest deployment

OR

1. Make a small commit to trigger auto-deploy (add a comment somewhere)

### 6. Verify Fix (5 minutes after deployment)

1. Go to: `https://backend-test-6a78.up.railway.app`
2. Open browser DevTools (F12)
3. Go to **Console** tab
4. Click **Quick Access** button
5. Check the console logs

**Before fix:**
```
accounts.google.com/gsi/button?...client_id=1008582896300-sbsrcs6jg32lncrnmmf1ia93vnl81tls...
Failed to load resource: 403
[GSI_LOGGER]: The given origin is not allowed for the given client ID.
```

**After fix (SUCCESS):**
```
accounts.google.com/gsi/button?...client_id=87279819935-i7a1r6kruor58op1jom3mhgcvkvpc7uh...
✓ No 403 errors
✓ Google Sign-In button loads successfully
```

---

## Complete Environment Variables Checklist

While you're in Railway's environment variables, verify these are all set correctly:

### Required Variables:

```bash
# Google OAuth (PUBLIC - UPDATED)
VITE_GOOGLE_CLIENT_ID=87279819935-i7a1r6kruor58op1jom3mhgcvkvpc7uh.apps.googleusercontent.com

# Firebase Config (PUBLIC)
VITE_FIREBASE_API_KEY=AIzaSyCGpr8w2sPsngexBYBg6ktNE64IWENtD2Q
VITE_FIREBASE_AUTH_DOMAIN=report-automation-57f6e.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=report-automation-57f6e
VITE_FIREBASE_STORAGE_BUCKET=report-automation-57f6e.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=87279819935
VITE_FIREBASE_APP_ID=1:87279819935:web:9f78b1c4c2efe16ad4d6aa
VITE_FIREBASE_MEASUREMENT_ID=G-R2HGN102D3

# Backend API
VITE_API_URL=https://backend-test-6a78.up.railway.app

# Environment
VITE_ENVIRONMENT=production
VITE_NODE_ENV=production
```

### Optional (Set Later):

```bash
# reCAPTCHA (for Firebase Phone Auth)
VITE_RECAPTCHA_SITE_KEY=<your-recaptcha-site-key-from-google>

# App Check
VITE_APP_CHECK_ENABLED=false
```

---

## Why This Happened

1. **Local `.env`** → Used for local development (`npm run dev`)
2. **`.env.production`** → Used for production builds (`npm run build`)
3. Railway runs `npm run build`, which reads `.env.production`
4. `.env.production` is in `.gitignore` (correct for security)
5. Railway needs environment variables configured in **Dashboard**, not in git

---

## Timeline

1. **Update Railway variable**: 2 minutes
2. **Railway redeploy**: 3-5 minutes (automatic)
3. **Verify fix**: 1 minute
4. **Total**: ~8 minutes

---

## After This Fix

Once this is fixed, you still need to complete the OAuth and reCAPTCHA configuration from [FINAL_CONFIGURATION_STEPS.md](FINAL_CONFIGURATION_STEPS.md):

1. ✅ Fix Google Client ID in Railway ← **DO THIS NOW**
2. ⏳ Configure Google OAuth authorized origins
3. ⏳ Generate reCAPTCHA site key
4. ⏳ Add reCAPTCHA key to Railway

---

## If Railway Auto-Deploy Doesn't Trigger

If changing the environment variable doesn't trigger a rebuild, you can force it by making a trivial commit:

```bash
# Add a comment to trigger rebuild
echo "# Trigger rebuild" >> frontend/README.md
git add frontend/README.md
git commit -m "Trigger Railway rebuild after env var update"
git push origin Test5
```

Railway will detect the push and redeploy with the new environment variables.

---

## Need Help?

- **Railway Docs**: https://docs.railway.app/guides/variables
- **Check Build Logs**: Railway Dashboard → Deployments → View Logs
- **Check Environment Variables**: Railway Dashboard → Variables tab

---

**Action Required**: Update `VITE_GOOGLE_CLIENT_ID` in Railway Dashboard NOW to fix production! 🚨
