# Fix Summary: 500 Error on /api/v1/nextgen/excel/generate-report

## Problem Identified

Based on your error logs, the root cause was:

### Template ID Type Mismatch
- **Frontend sends**: String template name (e.g., `"04- LAPORAN FU _ PUNCAK ALAM_final"`)
- **Backend expects**: Integer ID for database lookup
- **Error**: `invalid literal for int() with base 10: '04- LAPORAN FU _ PUNCAK ALAM_final'`

This caused the database template lookup to fail, and while the filesystem fallback worked, subsequent database operations may have been affected by the failed transaction.

## Fixes Applied

### 1. Enhanced Authentication Error Handling
**File**: [backend/app/decorators.py](backend/app/decorators.py#L97-L124)

**Changes**:
- Added comprehensive error logging for authentication failures
- Changed HTTP status from 500 to 401 for auth errors
- Added error details including type, timestamp, and Firebase initialization status

**Why**: Auth errors should return 401 (Unauthorized), not 500 (Internal Server Error)

### 2. Flexible Template Lookup
**File**: [backend/app/routes/nextgen_report_builder.py](backend/app/routes/nextgen_report_builder.py#L1190-L1238)

**Changes**:
- Added dual-mode template lookup (integer ID or string name)
- Try integer lookup first (for numeric IDs)
- Fall back to name-based lookup (for string template names)
- Support partial matching on file_path
- Better error logging for each lookup attempt

**Example**:
```python
# Now handles both:
template_id = 123  # Integer ID lookup
template_id = "04- LAPORAN FU _ PUNCAK ALAM_final"  # Name-based lookup
```

### 3. Clean Template Name Handling
**File**: [backend/app/routes/nextgen_report_builder.py](backend/app/routes/nextgen_report_builder.py#L1650-L1662)

**Changes**:
- Strip file extensions (.docx, .jinja, .tex, .html) before database insertion
- Use cleaned name for better matching
- More descriptive auto-generated template records

**Before**:
```python
template_data = {
    'name': '04- LAPORAN FU _ PUNCAK ALAM_final.docx',  # With extension
}
```

**After**:
```python
template_data = {
    'name': '04- LAPORAN FU _ PUNCAK ALAM_final',  # Extension removed
}
```

### 4. Optional Foreign Keys in Report Creation
**File**: [backend/app/routes/nextgen_report_builder.py](backend/app/routes/nextgen_report_builder.py#L1842-L1854)

**Changes**:
- Made `program_id` and `template_id` optional in report creation
- Only include if valid values are available
- Prevents foreign key constraint errors
- Better error messages when IDs are missing

### 5. Dynamic SQL Insert
**File**: [backend/app/routes/nextgen_report_builder.py](backend/app/routes/nextgen_report_builder.py#L1869-L1881)

**Changes**:
- Build SQL INSERT statement dynamically based on available fields
- Only include columns that have values
- Prevents SQL errors from missing required fields

**Before**:
```sql
INSERT INTO reports (title, ..., program_id, template_id, ...)
VALUES (:title, ..., :program_id, :template_id, ...)
-- Fails if program_id or template_id is NULL
```

**After**:
```python
# Dynamically builds SQL based on available fields
columns = list(safe_report_data.keys())  # Only includes non-null fields
INSERT INTO reports (title, description, ...)
VALUES (:title, :description, ...)
```

## Testing Recommendations

### Test Case 1: String Template Name
```bash
curl -X POST https://backend-test-6a78.up.railway.app/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "excelFilePath": "/path/to/excel.xlsx",
    "templateId": "04- LAPORAN FU _ PUNCAK ALAM_final",
    "reportTitle": "Test Report"
  }'
```

**Expected**: Should work without integer conversion errors

### Test Case 2: Integer Template ID
```bash
curl -X POST https://backend-test-6a78.up.railway.app/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "excelFilePath": "/path/to/excel.xlsx",
    "templateId": 123,
    "reportTitle": "Test Report"
  }'
```

**Expected**: Should work with integer ID lookup

### Test Case 3: Template Not in Database
```bash
curl -X POST https://backend-test-6a78.up.railway.app/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "excelFilePath": "/path/to/excel.xlsx",
    "templateId": "NonExistentTemplate",
    "reportTitle": "Test Report"
  }'
```

**Expected**: Should fall back to filesystem lookup, then create template record if needed

## Log Monitoring

After deployment, check Railway logs for:

### Success Indicators:
```
✅ Looking up template: 04- LAPORAN FU _ PUNCAK ALAM_final (type: str)
🔍 Template ID is not numeric, trying name-based lookup
✅ Found template by name in database
✅ Using template_id: 123
✅ Report created successfully with ID: 456
```

### Error Indicators to Watch:
```
❌ Template query failed
❌ Database error creating report
⚠️ No valid template_id available
⚠️ No valid program_id available
```

## Database Schema Notes

If you continue to have issues, verify your database schema:

```sql
-- Check if these columns allow NULL
DESCRIBE reports;

-- Verify template table structure
DESCRIBE templates;

-- Check foreign key constraints
SHOW CREATE TABLE reports;
```

## Next Steps

1. **Deploy changes** to Railway
2. **Test with actual request** from frontend
3. **Monitor Railway logs** for the new detailed logging
4. **Verify report creation** in database

## Related Files Modified

1. [backend/app/decorators.py](backend/app/decorators.py) - Auth error handling
2. [backend/app/routes/nextgen_report_builder.py](backend/app/routes/nextgen_report_builder.py) - Template lookup and report creation
3. [backend/error_investigation_guide.md](backend/error_investigation_guide.md) - Debugging guide

## Rollback Plan

If issues persist, revert changes:
```bash
git diff HEAD backend/app/decorators.py
git diff HEAD backend/app/routes/nextgen_report_builder.py
git checkout HEAD -- backend/app/decorators.py backend/app/routes/nextgen_report_builder.py
```

## Contact

If you encounter any issues after deployment, provide:
1. Full Railway log output
2. Request payload from frontend
3. Any new error messages
