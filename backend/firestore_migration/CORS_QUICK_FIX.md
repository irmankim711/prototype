# 🚨 Quick Fix: Firebase Storage CORS Issue

## Problem Summary
Your frontend at `https://stratosys.com.my` is blocked from downloading files from Firebase Storage because the storage bucket doesn't allow cross-origin requests from your domain.

## Quick Fix (5 minutes)

### Step 1: Install Google Cloud SDK
If you don't have it already:
- **Windows**: Download from https://cloud.google.com/sdk/docs/install
- **Mac**: `brew install google-cloud-sdk`
- **Linux**: `curl https://sdk.cloud.google.com | bash`

### Step 2: Authenticate
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 3: Apply CORS Configuration
```bash
cd backend/firestore_migration
gsutil cors set cors.json gs://YOUR_BUCKET_NAME
```

Your bucket name is typically: `YOUR_PROJECT_ID.appspot.com`

### Step 4: Verify
```bash
gsutil cors get gs://YOUR_BUCKET_NAME
```

### Step 5: Test
Clear browser cache and try downloading a file from https://stratosys.com.my

## Current Flow (Why This Happens)

```
Frontend (stratosys.com.my)
    ↓
Backend API (/api/reports/<id>/download)
    ↓
Firebase Storage (generates signed URL)
    ↓
Returns signed URL to frontend
    ↓
Frontend tries to download from storage.googleapis.com
    ↓
❌ BLOCKED BY CORS (because storage bucket doesn't allow stratosys.com.my)
```

## What the CORS Config Does

The `cors.json` file tells Firebase Storage to accept requests from:
- `https://stratosys.com.my`
- `https://www.stratosys.com.my`

## Need Help?

See full documentation in `FIREBASE_STORAGE_CORS_SETUP.md`

## Alternative: Backend Proxy (If CORS Config Not Possible)

If you can't configure CORS, modify the download endpoint to proxy the file through your backend instead of returning a signed URL. This means:

1. Backend downloads file from Firebase Storage
2. Backend streams file to frontend
3. No CORS issue (same-origin request)

**Trade-offs:**
- ✅ No CORS configuration needed
- ❌ Higher backend load
- ❌ Slower downloads
- ❌ Higher bandwidth costs

Contact your Firebase administrator if you need help with CORS configuration.
