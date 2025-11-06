# Foreign Key Constraint Violation Fix

## Problem
The code was trying to insert records into `excel_tables` with a `parsed_file_id` that did not exist in the `parsed_excel_files` table, causing a foreign key constraint violation:

```
psycopg2.errors.ForeignKeyViolation: insert or update on table "excel_tables" violates foreign key constraint "excel_tables_parsed_file_id_fkey"
DETAIL:  Key (parsed_file_id)=(2cb2e69f-1377-4ad1-8c35-5a7a52c1466e) is not present in table "parsed_excel_files".
```

## Root Cause
The code flow was:
1. Create `ParsedExcelFile` object and add to session
2. Create multiple `ExcelTable` objects and add to session
3. Call `db.session.commit()`

If the `ParsedExcelFile` insert failed or the transaction was rolled back before commit, the `ExcelTable` records would still try to reference a non-existent parent record.

## Solution
Fixed in two files:
1. `backend/app/routes/nextgen_report_builder.py` - Main Excel upload route
2. `backend/app/routes/excel_routes.py` - Alternative Excel upload route

### Key Changes:

1. **Added `db.session.flush()` after inserting parent record**
   - Ensures `ParsedExcelFile` is inserted into the database before adding child records
   - Validates the parent record exists before foreign key constraints are checked

2. **Added duplicate record cleanup**
   - Checks if a file with the same ID already exists
   - Deletes existing child records first (due to foreign key constraint)
   - Deletes existing parent record
   - Prevents conflicts on retries

3. **Enhanced error handling**
   - Catches `IntegrityError` and `DatabaseError` separately
   - Provides specific error messages for foreign key violations
   - Properly rolls back transactions on errors
   - Cleans up uploaded files on failure

4. **Better logging**
   - Logs when parent record is flushed
   - Logs specific error types
   - Provides detailed error information for debugging

## Code Changes

### Before:
```python
parsed_file = ParsedExcelFile(...)
db.session.add(parsed_file)

for table in tables:
    excel_table = ExcelTable(parsed_file_id=file_id, ...)
    db.session.add(excel_table)

db.session.commit()  # ❌ Parent might not exist if commit fails
```

### After:
```python
# Check for existing records
existing_file = ParsedExcelFile.query.filter_by(id=file_id).first()
if existing_file:
    ExcelTable.query.filter_by(parsed_file_id=file_id).delete()
    db.session.delete(existing_file)
    db.session.flush()

# Create parent record
parsed_file = ParsedExcelFile(...)
db.session.add(parsed_file)

# ✅ CRITICAL: Flush to ensure parent exists before children
try:
    db.session.flush()  # ✅ Parent is now in database
except IntegrityError as e:
    db.session.rollback()
    return error_response

# Create child records (parent now guaranteed to exist)
for table in tables:
    excel_table = ExcelTable(parsed_file_id=file_id, ...)
    db.session.add(excel_table)

db.session.commit()  # ✅ All records commit together
```

## Testing
To test the fix:
1. Upload an Excel file through the `/api/nextgen/excel/upload` endpoint
2. Verify the file is saved to the database
3. Check that all tables are properly linked to the parent file record
4. Try uploading the same file twice to test duplicate handling
5. Monitor logs for any foreign key constraint errors

## Prevention
This fix ensures:
- Parent record always exists before child records are inserted
- Transactions are properly handled with rollback on errors
- Duplicate uploads are handled gracefully
- Better error messages help identify issues quickly

## Firestore Sync

**NEW**: After successfully saving to SQL database, the code now also syncs to Firestore:

1. **Parent record first**: `ParsedExcelFile` is saved to Firestore before child records
2. **Child records second**: `ExcelTable` records are saved after parent exists
3. **Error handling**: Firestore sync failures don't fail the upload (SQL is source of truth)
4. **Same pattern**: Uses the same parent-then-child pattern as SQL to prevent reference errors

The Firestore sync happens automatically after a successful SQL commit, ensuring data consistency across both databases.

## Related Files
- `backend/app/models/production/excel_file_models.py` - Database models
- `backend/app/routes/nextgen_report_builder.py` - Main upload route (FIXED + Firestore sync added)
- `backend/app/routes/excel_routes.py` - Alternative upload route (FIXED)
- `backend/migrations/firestore_excel_migration.py` - Firestore migration script

