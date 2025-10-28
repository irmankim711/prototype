# Firebase Storage - Quick Setup Guide

## Step 1: Enable Firebase Storage (5 minutes)

### Open Firebase Console

1. **Go to**: https://console.firebase.google.com/
2. **Select your project**: `report-automation-57f6e`

### Enable Storage

3. **Click "Storage"** in the left sidebar (it has a folder icon)
4. **Click "Get started"** button
5. You'll see a dialog with security rules:

   ```
   Start in production mode
   ○ Start in test mode (not recommended)
   ● Start in production mode
   ```

6. **Select "Start in production mode"** (we'll set proper rules)
7. **Click "Next"**

### Choose Storage Location

8. You'll see "Set up Cloud Storage location"
9. **Select location**: Choose `us-central1` (or closest to your users)
10. **Click "Done"**

✅ **Storage is now enabled!** You should see the Storage dashboard.

---

## Step 2: Configure Security Rules

### Update Storage Rules

1. In the Firebase Console Storage page, click the **"Rules"** tab
2. Replace the default rules with:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Reports - authenticated users can read, only backend can write
    match /reports/{reportId}/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if false;  // Only backend service account can write
    }

    // User avatars - users can manage their own
    match /avatars/{userId}/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId;
    }

    // Temporary uploads - for testing
    match /temp/{allPaths=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

3. **Click "Publish"**

✅ **Security rules configured!**

---

## Step 3: Verify Your Service Account Has Access

Your service account already has full access because it's an Admin SDK service account. No additional configuration needed!

**Your service account**:
- File: `service/report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json`
- Email: `firebase-adminsdk-fbsvc@report-automation-57f6e.iam.gserviceaccount.com`

✅ **Service account ready!**

---

## Step 4: Get Your Storage Bucket Name

1. In Firebase Console → Storage, look at the top
2. You'll see something like: `gs://report-automation-57f6e.appspot.com`
3. Your bucket name is: `report-automation-57f6e.appspot.com`

**Note**: The Python SDK automatically uses this bucket name from your service account, so you don't need to configure it!

---

## Step 5: Test the Integration

Run the test script I'll create for you:

```bash
cd backend
python test_firebase_storage.py
```

This will:
- ✅ Verify Firebase Storage is accessible
- ✅ Upload a test file
- ✅ Download the test file
- ✅ Generate a signed URL
- ✅ Delete the test file

---

## Common Issues & Solutions

### Issue: "Permission denied" error

**Solution**: Make sure you've published the security rules in Step 2

### Issue: "Storage bucket not found"

**Solution**:
1. Check that Storage is enabled in Firebase Console
2. Wait 1-2 minutes after enabling for it to propagate
3. Restart your backend server

### Issue: "Service account lacks permissions"

**Solution**: Your service account should have the "Firebase Admin SDK Administrator Service Agent" role. Check in:
- Firebase Console → Project Settings → Service Accounts

---

## Verification Checklist

After setup, verify:

- [ ] Storage is enabled in Firebase Console
- [ ] You can see the "Storage" section with "Files" tab
- [ ] Security rules are published
- [ ] Test script runs successfully
- [ ] Backend logs show: "✅ Firebase Storage initialized successfully"

---

## Next Steps

Once setup is complete:

1. ✅ Run the test script (I'll create it)
2. ✅ Test creating a report with file upload
3. ✅ Update your report generation routes to use the new services

---

## Need Help?

If you encounter any issues, share:
- Firebase Console screenshot of Storage page
- Backend logs when starting the server
- Error messages from the test script
