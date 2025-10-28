# Firebase Console - Storage Setup Walkthrough

## 🎯 Goal
Enable Firebase Storage for your project so you can store report files in the cloud.

---

## 📋 Prerequisites
- ✅ You have access to Firebase Console
- ✅ Your project: `report-automation-57f6e`
- ✅ Service account is already set up

---

## 🚀 Step-by-Step Instructions

### Step 1: Open Firebase Console

1. **Open your browser** and go to:
   ```
   https://console.firebase.google.com/
   ```

2. **Sign in** with your Google account (if not already signed in)

3. **You'll see your projects** - Click on:
   ```
   report-automation-57f6e
   ```

---

### Step 2: Navigate to Storage

4. **On the left sidebar**, look for **"Storage"**
   - It has a folder icon 📁
   - It's usually below "Authentication" and "Firestore Database"

5. **Click "Storage"**

---

### Step 3: Enable Storage

You'll see one of two screens:

#### **If Storage is NOT enabled yet:**

You'll see a welcome screen with:
```
Get started with Cloud Storage for Firebase
Store and serve user-generated content...
```

6. **Click the "Get started" button**

7. **Security rules dialog appears:**
   - You'll see two options:
     ```
     ○ Start in test mode
     ● Start in production mode
     ```

8. **Select "Start in production mode"** (the second option)
   - This is more secure - we'll configure rules properly

9. **Click "Next"**

10. **Cloud Storage location dialog appears:**
    - You'll see a dropdown with regions
    - Recommended: `us-central1 (Iowa)` or closest to your location

11. **Select your preferred location**

12. **Click "Done"**

13. **Wait 10-30 seconds** while Firebase sets up Storage
    - You'll see a loading spinner

14. **✅ Success!** You'll now see the Storage dashboard

---

### Step 4: Configure Security Rules

15. **Click the "Rules" tab** at the top (next to "Files")

16. **You'll see default rules** that look like:
    ```javascript
    rules_version = '2';
    service firebase.storage {
      match /b/{bucket}/o {
        match /{allPaths=**} {
          allow read, write: if false;
        }
      }
    }
    ```

17. **Replace ALL the text** with these rules:
    ```javascript
    rules_version = '2';
    service firebase.storage {
      match /b/{bucket}/o {
        // Reports - authenticated users can read, only backend can write
        match /reports/{reportId}/{allPaths=**} {
          allow read: if request.auth != null;
          allow write: if false;
        }

        // User avatars
        match /avatars/{userId}/{allPaths=**} {
          allow read: if request.auth != null;
          allow write: if request.auth != null && request.auth.uid == userId;
        }

        // Test files
        match /test/{allPaths=**} {
          allow read, write: if request.auth != null;
        }
      }
    }
    ```

18. **Click "Publish"** button in the top right

19. **Confirm** if asked "Publish new rules?"

20. **✅ Rules published!** You'll see a success message

---

### Step 5: Verify Setup

21. **Click the "Files" tab** at the top

22. **You should see:**
    ```
    No files yet
    Upload your first file
    ```
    - This is normal! The bucket is empty and ready to use

23. **Note your bucket name** at the top:
    ```
    gs://report-automation-57f6e.appspot.com
    ```
    - This is automatically used by your service account

---

## ✅ Verification Checklist

After completing these steps, verify:

- [ ] **Storage tab** is visible in left sidebar
- [ ] **Files tab** shows "No files yet" (empty bucket)
- [ ] **Rules tab** shows your custom rules
- [ ] **Bucket name** visible at top: `gs://report-automation-57f6e.appspot.com`

---

## 🧪 Test Your Setup

Now run the test script from your backend folder:

```bash
cd backend
python test_firebase_storage.py
```

**Expected output:**
```
======================================================================
Firebase Storage & Firestore Reports - Integration Test
======================================================================

[Step 1] Loading environment...
✅ FIREBASE_SERVICE_ACCOUNT_PATH=service/...

[Step 2] Creating Flask app...
✅ Flask application created successfully

[Step 3] Testing Firebase Storage Service...
✅ Firebase Storage initialized
   Bucket: report-automation-57f6e.appspot.com

[Step 4] Creating test file...
✅ Created test file: C:\Users\...\test_report.txt

[Step 5] Uploading test file to Firebase Storage...
✅ Upload successful!
   Storage path: test/test_report.txt
   Download URL: https://storage.googleapis.com/...

... (more tests) ...

======================================================================
🎉 ALL TESTS PASSED!
======================================================================
```

---

## 🎉 Success! What Now?

Your Firebase Storage is ready! Now you can:

1. ✅ Store report files in the cloud
2. ✅ Generate secure download links
3. ✅ Track reports in Firestore
4. ✅ Give users access to their reports

---

## 🆘 Troubleshooting

### ❌ "Storage not enabled" error

**Solution:**
- Go back to Step 2-3
- Make sure you clicked "Get started" and completed the setup
- Wait 1-2 minutes and try again

### ❌ "Permission denied" error

**Solution:**
- Check that you published the security rules (Step 17-19)
- Make sure rules include `allow write: if false` for reports (backend-only writes)

### ❌ "Bucket not found" error

**Solution:**
- Check your Firebase project is correct: `report-automation-57f6e`
- Verify your service account file path is correct
- Restart your backend server

### ❌ Test script fails

**Solution:**
1. Check Firebase Console → Storage → Files tab
2. Check if "test/" folder appears
3. Share the error message from the test script
4. Check backend terminal logs

---

## 📞 Need Help?

If you're stuck:
1. **Take a screenshot** of the Firebase Console Storage page
2. **Run** `python test_firebase_storage.py` and share the output
3. **Share** any error messages from your backend logs

I'm here to help! 🚀
