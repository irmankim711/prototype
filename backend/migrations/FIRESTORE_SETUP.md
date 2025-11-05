# Firestore Migration Setup Guide

## Problem

The Firestore migration script requires Firebase credentials to run. You're seeing this error:

```
⚠️ Missing required environment variables: ['FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL']
```

---

## Solution Options

### Option 1: Set Up Firebase Environment Variables (Recommended)

#### Step 1: Get Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Click the gear icon ⚙️ → Project settings
4. Navigate to **Service accounts** tab
5. Click **Generate new private key**
6. Save the JSON file (e.g., `firebase-credentials.json`)

#### Step 2: Extract Credentials

Open the downloaded JSON file. You'll see something like:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com",
  ...
}
```

#### Step 3: Set Environment Variables

**Windows (PowerShell)**:
```powershell
# Set for current session
$env:FIREBASE_PROJECT_ID="your-project-id"
$env:FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----\n"
$env:FIREBASE_CLIENT_EMAIL="firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com"

# Or permanently (requires restart)
[System.Environment]::SetEnvironmentVariable('FIREBASE_PROJECT_ID', 'your-project-id', 'User')
[System.Environment]::SetEnvironmentVariable('FIREBASE_CLIENT_EMAIL', 'your-email', 'User')
# Note: For PRIVATE_KEY, use a .env file instead
```

**Windows (Command Prompt)**:
```cmd
set FIREBASE_PROJECT_ID=your-project-id
set FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----\n
set FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com
```

**Linux/Mac**:
```bash
export FIREBASE_PROJECT_ID="your-project-id"
export FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----\n"
export FIREBASE_CLIENT_EMAIL="firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com"
```

#### Step 4: Create .env File (Better Approach)

Create `backend/.env` file:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com

# Or use credentials file path
GOOGLE_APPLICATION_CREDENTIALS=./firebase-credentials.json
```

**Load .env file**:
```bash
# Install python-dotenv if not installed
pip install python-dotenv

# Run migration with .env
python -c "from dotenv import load_dotenv; load_dotenv(); exec(open('migrations/firestore_excel_migration.py').read())"
```

#### Step 5: Run Migration

```bash
cd backend
python migrations/firestore_excel_migration.py
```

**Expected Output**:
```
============================================================
FIRESTORE MIGRATION: ParsedExcelFiles Collection
============================================================
✅ Firebase initialized successfully

📁 Collections:
   - parsed_excel_files
   - excel_tables

🔄 Migrating existing SQL data to Firestore...
✅ Migration complete: Migrated 0 files
```

---

### Option 2: Use Firebase Credentials File

#### Step 1: Place Credentials File

```bash
# Copy your firebase-credentials.json to backend directory
cp ~/Downloads/firebase-credentials.json backend/firebase-credentials.json
```

#### Step 2: Set Environment Variable

```bash
export GOOGLE_APPLICATION_CREDENTIALS="./firebase-credentials.json"
```

#### Step 3: Run Migration

```bash
cd backend
python migrations/firestore_excel_migration.py
```

---

### Option 3: Skip Firestore Migration (SQL Only)

If you only want SQL database support (without Firestore sync):

#### Step 1: Run SQL Migration Only

```bash
cd backend
sqlite3 instance/app.db < migrations/add_excel_file_tracking.sql
```

#### Step 2: Verify Tables

```bash
sqlite3 instance/app.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%excel%';"
```

**Expected Output**:
```
parsed_excel_files
excel_tables
```

#### Step 3: Test Backend

The multi-file feature will work **without Firestore**. Data will be stored in SQL database only.

**Trade-offs**:
- ✅ Faster setup (no Firebase required)
- ✅ All core features work
- ❌ No real-time sync across devices
- ❌ No cloud backup of file metadata
- ❌ No offline support with Firestore caching

---

### Option 4: Manual Firestore Setup (Firebase Console)

If you prefer not to run the migration script:

#### Step 1: Create Collections Manually

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Navigate to: Firestore Database
3. Click **Start collection**

**Collection 1**: `parsed_excel_files`
- Add a test document with these fields:
  - `id` (string): "test-id"
  - `user_id` (string): "test-user"
  - `original_filename` (string): "test.xlsx"
  - `file_path` (string): "/path/to/file"
  - `file_size` (number): 1024
  - `status` (string): "completed"
  - `uploaded_at` (timestamp): Now
  - `tables_count` (number): 1
  - `total_rows` (number): 10
  - `total_columns` (number): 5

**Collection 2**: `excel_tables`
- Add a test document with these fields:
  - `id` (string): "test-table-id"
  - `parsed_file_id` (string): "test-id"
  - `name` (string): "Sheet1"
  - `sheet_name` (string): "Sheet1"
  - `row_count` (number): 10
  - `column_count` (number): 5
  - `created_at` (timestamp): Now

#### Step 2: Delete Test Documents

After verifying the structure, delete the test documents.

#### Step 3: Deploy Indexes

```bash
cd backend
firebase deploy --only firestore:indexes
```

#### Step 4: Deploy Rules

```bash
firebase deploy --only firestore:rules
```

---

## Verification

### Check Firebase Is Working

```python
# Test script: test_firebase_connection.py
from app.middleware.firebase_auth import firebase_auth_manager

if firebase_auth_manager._initialized:
    print("✅ Firebase is initialized")

    if firebase_auth_manager._firestore_db:
        print("✅ Firestore is available")

        # Try to write a test document
        try:
            test_ref = firebase_auth_manager._firestore_db.collection('test').document('test')
            test_ref.set({'test': 'value', 'timestamp': firebase_auth_manager._firestore_db.SERVER_TIMESTAMP})
            print("✅ Firestore write successful")

            # Clean up
            test_ref.delete()
            print("✅ Test document deleted")
        except Exception as e:
            print(f"❌ Firestore write failed: {e}")
    else:
        print("❌ Firestore not available")
else:
    print("❌ Firebase not initialized")
```

Run it:
```bash
cd backend
python test_firebase_connection.py
```

---

## Troubleshooting

### Error: "Firebase not initialized"

**Cause**: Missing environment variables

**Solution**: Set the required environment variables (see Option 1)

---

### Error: "Invalid credentials"

**Cause**: Wrong credentials or expired service account

**Solution**:
1. Download a fresh service account key from Firebase Console
2. Verify the JSON structure is correct
3. Ensure no extra spaces or newlines in the private key

---

### Error: "Permission denied"

**Cause**: Service account doesn't have sufficient permissions

**Solution**:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Click on your service account email
3. Go to IAM & Admin in Google Cloud Console
4. Add these roles:
   - Firebase Admin
   - Cloud Datastore User
   - Service Account Token Creator

---

### Error: "Collection already exists"

**Cause**: Collections were created previously

**Solution**: This is fine! The migration will skip existing documents.

---

## Quick Start (Recommended Path)

If you're new to this, follow these steps:

1. **Skip Firestore for now** - Run SQL migration only:
   ```bash
   sqlite3 instance/app.db < migrations/add_excel_file_tracking.sql
   ```

2. **Test the feature** - Upload files and generate reports

3. **Add Firestore later** - Once the feature is working, set up Firebase and run the migration

This approach lets you test the core functionality without Firebase complexity.

---

## Summary

| Method | Setup Time | Requires Firebase | Best For |
|--------|-----------|-------------------|----------|
| **SQL Only** | 2 min | ❌ No | Quick testing, local development |
| **Firebase + SQL** | 15 min | ✅ Yes | Production, cloud sync, real-time |
| **Manual Firestore** | 10 min | ✅ Yes | Custom setup, learning |

**Recommendation**: Start with **SQL Only**, then add Firebase when needed.

---

## Next Steps

After choosing your approach:

1. ✅ Run database migration (SQL or SQL+Firestore)
2. ✅ Restart backend server
3. ✅ Test file upload: `curl -X POST .../excel/upload -F "file=@test.xlsx"`
4. ✅ Test file listing: `curl .../excel/user-files`
5. ✅ Test report generation with file IDs

---

**Need Help?**
- Check backend logs: `tail -f logs/app.log`
- Verify Firebase Console for errors
- Review implementation guide: MULTI_FILE_EXCEL_IMPLEMENTATION.md
