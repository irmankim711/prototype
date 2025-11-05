# Multi-File Excel Processing - Deployment Guide

## Overview

This guide provides step-by-step instructions to deploy the multi-file Excel processing feature, including database migrations, Firestore setup, and testing procedures.

---

## Prerequisites

Before deploying, ensure you have:

- [x] Backend running with Python 3.8+
- [x] Frontend running with Node.js 16+
- [x] SQLite/MySQL database access
- [x] Firebase/Firestore configured
- [x] Admin/deployment credentials

---

## Part 1: Backend Deployment

### Step 1: Run SQL Database Migration

```bash
cd backend

# Option A: SQLite (Development)
sqlite3 instance/app.db < migrations/add_excel_file_tracking.sql

# Option B: MySQL (Production)
mysql -u username -p database_name < migrations/add_excel_file_tracking.sql

# Option C: Using Flask-Migrate
python manage.py db upgrade
```

**Verify Migration**:
```bash
# SQLite
sqlite3 instance/app.db "SELECT name FROM sqlite_master WHERE type='table';"

# MySQL
mysql -u username -p -e "SHOW TABLES LIKE 'parsed_excel_files';" database_name
```

**Expected Output**:
```
parsed_excel_files
excel_tables
```

---

### Step 2: Run Firestore Migration

```bash
cd backend/migrations

# Run the Firestore migration script
python firestore_excel_migration.py
```

**Expected Output**:
```
==============================================================
FIRESTORE MIGRATION: ParsedExcelFiles Collection
==============================================================
✅ Firebase initialized successfully

📁 Collections:
   - parsed_excel_files
   - excel_tables

🔄 Migrating existing SQL data to Firestore...

📊 Found 0 files in SQL database

✅ Migration complete:
   - Migrated: 0 files
   - Errors: 0

==============================================================
✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!
==============================================================
```

---

### Step 3: Deploy Firestore Indexes

```bash
# Copy the index configuration to your Firebase project
cp migrations/firestore.indexes.json ./firestore.indexes.json

# Deploy indexes using Firebase CLI
firebase deploy --only firestore:indexes
```

**Verify Indexes**:
- Go to [Firebase Console](https://console.firebase.google.com/)
- Navigate to: Firestore Database → Indexes
- Confirm these composite indexes exist:
  1. `parsed_excel_files`: `user_id` (ASC) + `uploaded_at` (DESC)
  2. `parsed_excel_files`: `user_id` (ASC) + `status` (ASC) + `uploaded_at` (DESC)
  3. `excel_tables`: `parsed_file_id` (ASC) + `created_at` (DESC)

---

### Step 4: Deploy Firestore Security Rules

```bash
# Copy the rules to your Firebase project
cp migrations/firestore.rules ./firestore.rules

# Deploy security rules
firebase deploy --only firestore:rules
```

**Verify Rules**:
- Go to: Firestore Database → Rules
- Confirm rules allow:
  - Users can only read/write their own `parsed_excel_files`
  - Users can read `excel_tables` if they own the parent file

---

### Step 5: Restart Backend Server

```bash
cd backend

# Development
flask run

# Production (example with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Railway/Heroku will auto-restart on git push
```

---

## Part 2: Frontend Deployment

### Step 1: Install Frontend Dependencies

```bash
cd frontend

# Install any new dependencies (if needed)
npm install
```

---

### Step 2: Build Frontend

```bash
# Development build
npm run build:dev

# Production build
npm run build
```

---

### Step 3: Deploy Frontend

```bash
# Option A: Deploy to existing host
npm run deploy

# Option B: Railway/Netlify (automatic via git push)
git add .
git commit -m "feat: Add multi-file Excel processing"
git push origin main
```

---

## Part 3: Testing

### Test 1: Verify Database Tables

```bash
# Check tables exist
python -c "
from app.models import ParsedExcelFile, ExcelTable, db
print(f'ParsedExcelFile: {ParsedExcelFile.query.count()} records')
print(f'ExcelTable: {ExcelTable.query.count()} records')
"
```

**Expected Output**:
```
ParsedExcelFile: 0 records
ExcelTable: 0 records
```

---

### Test 2: Test File Upload (Backend)

```bash
# Create a test Excel file
echo "Name,Age,City
John,30,NYC
Jane,25,LA" > test.csv

# Convert to Excel (or use existing .xlsx file)

# Upload file via curl
curl -X POST http://localhost:5000/api/v1/nextgen/excel/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.xlsx"
```

**Expected Response**:
```json
{
  "success": true,
  "fileId": "abc123-def456-...",
  "dataSource": {
    "id": "abc123...",
    "fileId": "abc123...",
    "name": "test.xlsx",
    "recordCount": 2,
    "fields": [...]
  }
}
```

---

### Test 3: Test File Listing

```bash
curl http://localhost:5000/api/v1/nextgen/excel/user-files \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response**:
```json
{
  "success": true,
  "files": [
    {
      "id": "abc123...",
      "name": "test.xlsx",
      "totalRows": 2,
      "totalColumns": 3,
      "uploadedAt": "2025-01-05T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "totalPages": 1,
    "totalFiles": 1
  }
}
```

---

### Test 4: Test Single-File Report Generation (New Method)

```bash
curl -X POST http://localhost:5000/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "abc123...",
    "templateId": "template_name",
    "reportTitle": "Test Report"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "reportId": 123,
  "reportTitle": "Test Report",
  "status": "completed",
  "report": {
    "id": 123,
    "download_url": "/static/generated/report_template_name_20250105_103000.docx"
  }
}
```

---

### Test 5: Test Multi-File Report Generation

```bash
# Upload second file first
curl -X POST http://localhost:5000/api/v1/nextgen/excel/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test2.xlsx"

# Generate report from multiple files
curl -X POST http://localhost:5000/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fileIds": ["file-id-1", "file-id-2"],
    "templateId": "template_name",
    "reportTitle": "Combined Report"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "reportId": 124,
  "reportTitle": "Combined Report",
  "status": "completed",
  "report": {
    "id": 124,
    "excelSource": "multiple_files"
  }
}
```

---

### Test 6: Test Backward Compatibility (Legacy Path Mode)

```bash
curl -X POST http://localhost:5000/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type": application/json" \
  -d '{
    "excelFilePath": "/path/to/uploaded/file.xlsx",
    "templateId": "template_name",
    "reportTitle": "Legacy Report"
  }'
```

**Expected**: Should work exactly as before (backward compatible).

---

### Test 7: Frontend Integration Test

1. **Open Frontend**: Navigate to http://localhost:3000/report-builder
2. **Upload File**: Drag and drop an Excel file
3. **View Files**: Click "Show Previously Uploaded Files"
4. **Select Files**: Check multiple files (up to 10)
5. **Generate Report**: Click "Generate Report from X Files"
6. **Verify**: Report should be generated with merged data

---

## Part 4: Monitoring & Verification

### Check Backend Logs

```bash
# View recent logs
tail -f logs/app.log

# Search for Excel-related logs
grep "Excel" logs/app.log | tail -20

# Check for errors
grep "ERROR" logs/app.log | grep "Excel"
```

**Look for**:
```
✅ Saved Excel file to database: file_id=abc123...
🆕 Using file ID(s): ['abc123...', 'def456...']
✅ Multi-file data loaded: Files: 2, Total records: 200
```

---

### Check Firestore Data

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Navigate to: Firestore Database
3. Collections: `parsed_excel_files` and `excel_tables`
4. Verify documents exist with correct structure

---

### Check Database

```bash
# SQLite
sqlite3 instance/app.db "SELECT id, original_filename, status FROM parsed_excel_files LIMIT 5;"

# MySQL
mysql -u username -p -e "SELECT id, original_filename, status FROM parsed_excel_files LIMIT 5;" database_name
```

---

## Part 5: Rollback Procedure

If issues occur, follow these steps to rollback:

### Step 1: Rollback Database

```bash
cd backend/migrations

# Create rollback SQL (if not exists)
cat > rollback_excel_tracking.sql << 'EOF'
DROP TABLE IF EXISTS excel_tables;
DROP TABLE IF EXISTS parsed_excel_files;
EOF

# Run rollback
sqlite3 instance/app.db < rollback_excel_tracking.sql
```

---

### Step 2: Rollback Firestore (Optional)

```bash
# Delete collections via Firebase Console or script
python << 'EOF'
from app.middleware.firebase_auth import firebase_auth_manager

firestore_db = firebase_auth_manager._firestore_db
if firestore_db:
    # Delete parsed_excel_files collection
    docs = firestore_db.collection('parsed_excel_files').stream()
    for doc in docs:
        doc.reference.delete()

    # Delete excel_tables collection
    docs = firestore_db.collection('excel_tables').stream()
    for doc in docs:
        doc.reference.delete()

    print("✅ Firestore collections deleted")
EOF
```

---

### Step 3: Revert Code Changes

```bash
# Revert to previous commit
git log --oneline | head -5  # Find commit before multi-file feature
git revert <commit-hash>
git push origin main
```

---

## Part 6: Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_parsed_excel_user_date
ON parsed_excel_files(user_id, uploaded_at DESC);

CREATE INDEX idx_parsed_excel_status
ON parsed_excel_files(status, uploaded_at DESC);

CREATE INDEX idx_excel_tables_file
ON excel_tables(parsed_file_id, created_at DESC);
```

---

### Firestore Optimization

- Enable Firestore caching in frontend:
```typescript
import { initializeFirestore, persistentLocalCache } from 'firebase/firestore';

const firestore = initializeFirestore(app, {
  localCache: persistentLocalCache()
});
```

---

### File Upload Optimization

- Increase nginx upload size limit (if applicable):
```nginx
client_max_body_size 50M;
```

- Configure backend timeout:
```python
# In gunicorn config
timeout = 120  # 2 minutes for large files
```

---

## Part 7: Troubleshooting

### Issue: Tables not created

**Solution**:
```bash
# Check migration file syntax
cat migrations/add_excel_file_tracking.sql

# Run with verbose output
sqlite3 instance/app.db < migrations/add_excel_file_tracking.sql 2>&1 | tee migration.log
```

---

### Issue: Firestore permission denied

**Solution**:
1. Check `firestore.rules` deployed correctly
2. Verify user authentication token
3. Check `user_id` matches authenticated user

**Debug**:
```javascript
// In browser console
const user = firebase.auth().currentUser;
console.log('User ID:', user.uid);
```

---

### Issue: File upload fails

**Solution**:
1. Check file size < 50MB
2. Verify upload directory exists and is writable:
```bash
mkdir -p backend/static/uploads/excel
chmod 755 backend/static/uploads/excel
```

3. Check backend logs for specific error

---

### Issue: Multi-file report shows duplicate data

**Solution**:
- Check that `_source_file_id` field is being added to records
- Verify data merging logic in [nextgen_report_builder.py:1353-1358](backend/app/routes/nextgen_report_builder.py#L1353-L1358)

---

## Part 8: Success Criteria

Deployment is successful when:

- [x] Database tables created successfully
- [x] Firestore collections exist with correct schema
- [x] File upload returns `fileId` in response
- [x] GET `/excel/user-files` returns uploaded files
- [x] Single-file report generation works with `fileId`
- [x] Multi-file report generation works with `fileIds` array
- [x] Legacy path-based report generation still works
- [x] Frontend displays file selection UI
- [x] Users can select multiple files and generate reports
- [x] No errors in backend/frontend logs

---

## Part 9: Post-Deployment Monitoring

### Metrics to Monitor

1. **Upload Success Rate**:
   - Track: `parsed_excel_files.status = 'completed'` vs `'error'`
   - Target: > 95% success rate

2. **Report Generation Time**:
   - Single file: < 10 seconds
   - Multi-file (2-5 files): < 30 seconds
   - Multi-file (6-10 files): < 60 seconds

3. **Database Growth**:
   - Monitor `parsed_excel_files` table size
   - Set up cleanup job for old files (e.g., > 90 days)

4. **Error Rates**:
   - Track 400/500 errors in Excel endpoints
   - Set up alerts for error spikes

---

### Cleanup Script (Optional)

```python
# cleanup_old_excel_files.py
from app.models import ParsedExcelFile, db
from datetime import datetime, timedelta
import os

def cleanup_old_files(days=90):
    """Delete Excel files older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    old_files = ParsedExcelFile.query.filter(
        ParsedExcelFile.uploaded_at < cutoff_date
    ).all()

    for file in old_files:
        # Delete physical file
        if os.path.exists(file.file_path):
            os.remove(file.file_path)

        # Delete database record (cascade deletes tables)
        db.session.delete(file)

    db.session.commit()
    print(f"✅ Deleted {len(old_files)} old files")

if __name__ == '__main__':
    cleanup_old_files(90)
```

---

## Part 10: Documentation Updates

After successful deployment, update:

1. **API Documentation**: Add new endpoints to API docs
2. **User Guide**: Update with multi-file selection instructions
3. **Release Notes**: Document new feature and breaking changes (if any)
4. **Team Wiki**: Add troubleshooting guide and known issues

---

## Summary

**Deployment Steps**:
1. ✅ Run SQL migration → Create tables
2. ✅ Run Firestore migration → Create collections
3. ✅ Deploy Firestore indexes → Enable queries
4. ✅ Deploy Firestore rules → Secure data
5. ✅ Restart backend → Load new code
6. ✅ Build and deploy frontend → Update UI
7. ✅ Run tests → Verify functionality
8. ✅ Monitor logs → Check for errors

**Time Estimate**:
- SQL migration: 2 minutes
- Firestore setup: 10 minutes
- Backend deployment: 5 minutes
- Frontend deployment: 10 minutes
- Testing: 20 minutes
- **Total**: ~45 minutes

**Rollback Time**: ~10 minutes (if needed)

---

## Support

For issues or questions:
1. Check [MULTI_FILE_EXCEL_IMPLEMENTATION.md](MULTI_FILE_EXCEL_IMPLEMENTATION.md) for technical details
2. Review backend logs: `tail -f logs/app.log`
3. Check Firestore console for data issues
4. Contact: [Your team's support channel]

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Rollback Tested**: ☐ Yes ☐ No
**Success**: ☐ Yes ☐ No

---

End of Deployment Guide
