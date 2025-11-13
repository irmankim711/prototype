# Firebase Storage CORS Configuration Guide

## Problem
Your frontend at `https://stratosys.com.my` is blocked from downloading files from Firebase Storage due to CORS (Cross-Origin Resource Sharing) restrictions.

## Solution 1: Configure CORS on Firebase Storage (Recommended)

### Prerequisites
- Google Cloud SDK (gcloud) installed
- Access to your Firebase project
- Your Firebase project ID

### Step 1: Install Google Cloud SDK

**Windows:**
```bash
# Download and run the installer from:
# https://cloud.google.com/sdk/docs/install

# After installation, initialize gcloud
gcloud init
```

**Mac/Linux:**
```bash
# Install using the installer
curl https://sdk.cloud.google.com | bash

# Restart your shell
exec -l $SHELL

# Initialize gcloud
gcloud init
```

### Step 2: Authenticate with Google Cloud

```bash
# Login to your Google account
gcloud auth login

# Set your Firebase project ID (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID
```

### Step 3: Find Your Storage Bucket Name

Your storage bucket name is typically: `YOUR_PROJECT_ID.appspot.com`

You can verify it in the Firebase Console:
1. Go to https://console.firebase.google.com
2. Select your project
3. Go to Storage
4. The bucket name is shown at the top

### Step 4: Apply CORS Configuration

```bash
# Navigate to the firestore_migration directory
cd backend/firestore_migration

# Apply CORS configuration to your storage bucket
# Replace YOUR_BUCKET_NAME with your actual bucket name
gsutil cors set cors.json gs://YOUR_BUCKET_NAME
```

### Step 5: Verify CORS Configuration

```bash
# Check the current CORS configuration
gsutil cors get gs://YOUR_BUCKET_NAME
```

You should see output similar to:
```json
[
  {
    "origin": ["https://stratosys.com.my", "https://www.stratosys.com.my"],
    "method": ["GET", "HEAD", "PUT", "POST", "DELETE"],
    "maxAgeSeconds": 3600,
    "responseHeader": [
      "Content-Type",
      "Content-Disposition",
      "Content-Length",
      "Authorization",
      "X-Firebase-Storage-Version"
    ]
  }
]
```

### Step 6: Test the Fix

1. Clear your browser cache
2. Try downloading a file from your frontend at https://stratosys.com.my
3. The download should now work without CORS errors

## Adding Additional Domains

If you need to add more domains (e.g., for development or staging), edit `cors.json`:

```json
[
  {
    "origin": [
      "https://stratosys.com.my",
      "https://www.stratosys.com.my",
      "http://localhost:3000",
      "https://staging.stratosys.com.my"
    ],
    "method": ["GET", "HEAD", "PUT", "POST", "DELETE"],
    "maxAgeSeconds": 3600,
    "responseHeader": [
      "Content-Type",
      "Content-Disposition",
      "Content-Length",
      "Authorization",
      "X-Firebase-Storage-Version"
    ]
  }
]
```

Then reapply the configuration:
```bash
gsutil cors set cors.json gs://YOUR_BUCKET_NAME
```

## Troubleshooting

### Error: "gsutil: command not found"
- Google Cloud SDK is not installed or not in your PATH
- Solution: Install Google Cloud SDK following Step 1

### Error: "AccessDeniedException: 403"
- You don't have permission to modify the storage bucket
- Solution: Ensure you're logged in with an account that has Storage Admin or Owner role on the project

### Error: "BucketNotFoundException: 404"
- The bucket name is incorrect
- Solution: Verify your bucket name in the Firebase Console

### CORS Still Not Working After Configuration
1. Clear browser cache completely
2. Check browser console for exact CORS error message
3. Verify the CORS configuration was applied: `gsutil cors get gs://YOUR_BUCKET_NAME`
4. Ensure your frontend is making requests with proper headers
5. Check if your storage bucket rules allow public read access (if needed)

## Solution 2: Backend Proxy (Alternative)

If you can't configure CORS on Firebase Storage, you can proxy downloads through your backend. See the implementation guide below.

### Backend Proxy Implementation

This approach routes all downloads through your backend API, which then fetches from Firebase Storage and returns the file to the frontend.

**Advantages:**
- No CORS configuration needed
- Better control over access/authentication
- Can add logging and analytics

**Disadvantages:**
- Increased backend load
- Slower downloads (extra hop)
- Higher bandwidth costs on your server

The proxy solution is already implemented in your backend at `/api/reports/<id>/download` endpoint, which handles Firebase Storage downloads.

## Security Considerations

1. **CORS Configuration**: The CORS configuration allows specific origins only. Never use `"*"` for production.

2. **Storage Rules**: Ensure your Firebase Storage security rules are properly configured:
   ```
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {
       match /reports/{userId}/{reportId}/{fileName} {
         allow read: if request.auth != null && request.auth.uid == userId;
         allow write: if request.auth != null && request.auth.uid == userId;
       }
     }
   }
   ```

3. **Authentication**: Always require authentication for sensitive files.

## Additional Resources

- [Google Cloud CORS Documentation](https://cloud.google.com/storage/docs/configuring-cors)
- [Firebase Storage Security Rules](https://firebase.google.com/docs/storage/security)
- [gsutil CORS Configuration](https://cloud.google.com/storage/docs/gsutil/commands/cors)
