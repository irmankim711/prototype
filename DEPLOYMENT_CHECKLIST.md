# Deployment Checklist: 500 Error Fix

## Summary
Fixed the 500 Internal Server Error on `/api/v1/nextgen/excel/generate-report` endpoint caused by template ID type mismatch.

## Root Cause
Frontend sends string template names (e.g., `"04- LAPORAN FU _ PUNCAK ALAM_final"`), but backend expected integer IDs, causing `ValueError: invalid literal for int()`.

## Files Modified

### 1. backend/app/decorators.py
- Enhanced authentication error logging
- Changed auth error status from 500 to 401
- Added detailed error information for debugging

### 2. backend/app/routes/nextgen_report_builder.py
- Added flexible template lookup (handles both integer IDs and string names)
- Made program_id and template_id optional in database inserts
- Implemented dynamic SQL INSERT based on available fields
- Improved template name cleaning (removes file extensions)

## Pre-Deployment Testing

✅ All unit tests passed:
```bash
cd backend && python test_template_lookup_fix.py
```

Results:
- ✅ Integer template ID parsing
- ✅ String template name handling
- ✅ File extension removal
- ✅ Dynamic SQL without template_id
- ✅ Dynamic SQL with template_id

## Deployment Steps

### Step 1: Commit Changes
```bash
git add backend/app/decorators.py
git add backend/app/routes/nextgen_report_builder.py
git add backend/test_template_lookup_fix.py
git add FIX_SUMMARY_500_ERROR.md
git add backend/error_investigation_guide.md
git add DEPLOYMENT_CHECKLIST.md

git commit -m "fix: Handle both integer and string template IDs in report generation

- Add flexible template lookup supporting integer IDs and string names
- Make program_id and template_id optional in database inserts
- Implement dynamic SQL INSERT to handle optional fields
- Fix authentication error status (500 -> 401)
- Add comprehensive error logging for production debugging
- Clean template names by removing file extensions

Fixes #<issue-number> - 500 error on /api/v1/nextgen/excel/generate-report"
```

### Step 2: Push to Repository
```bash
git push origin Test5
```

### Step 3: Verify Railway Auto-Deploy
1. Go to Railway dashboard
2. Check deployment logs
3. Wait for successful deployment
4. Verify new version is live

### Step 4: Smoke Test on Production

**Test 1: String Template Name**
```bash
curl -X POST https://backend-test-6a78.up.railway.app/api/v1/nextgen/excel/generate-report \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "excelFilePath": "/app/uploads/test.xlsx",
    "templateId": "04- LAPORAN FU _ PUNCAK ALAM_final",
    "reportTitle": "Production Test Report"
  }'
```

**Expected Response**: 200 OK with report details

**Test 2: Check Railway Logs**
```bash
railway logs --tail 100
```

Look for:
- ✅ `Looking up template: 04- LAPORAN FU _ PUNCAK ALAM_final (type: str)`
- ✅ `Found template by name in database` or `Template not found in DB, falling back to filesystem`
- ✅ `Report created successfully with ID: <id>`

### Step 5: Monitor for Errors
Watch for these patterns in logs over next 24 hours:
- No more `invalid literal for int()` errors
- Auth errors return 401 instead of 500
- Template lookups succeed for both integer and string IDs

## Rollback Plan

If issues occur, rollback immediately:

```bash
# Revert the commit
git revert HEAD

# Or reset to previous commit
git reset --hard <previous-commit-hash>

# Force push to trigger Railway redeploy
git push origin Test5 --force
```

## Post-Deployment Verification

### Success Criteria
- [ ] No 500 errors on `/api/v1/nextgen/excel/generate-report`
- [ ] String template names work correctly
- [ ] Integer template IDs still work
- [ ] Reports are created in database
- [ ] Auth errors return 401 instead of 500
- [ ] Detailed error logs available in Railway

### Monitoring Metrics
Monitor these for 24-48 hours:
- Error rate on the endpoint (should drop to near 0%)
- Average response time (should remain under 5 seconds)
- Successful report generation rate
- Database foreign key constraint violations (should be 0)

## Known Limitations

1. **Template ID Ambiguity**: If a template name is purely numeric (e.g., "123"), it will be treated as an integer ID first
   - **Mitigation**: Ensure template names are descriptive strings

2. **Database Schema Dependencies**: The fix assumes `program_id` and `template_id` are nullable in the reports table
   - **Verification**: Check database schema with `DESCRIBE reports;`

3. **File Path Matching**: Partial file_path matching might return unexpected results if multiple templates have similar names
   - **Mitigation**: Use exact template names from the database

## Support Resources

- [Fix Summary](FIX_SUMMARY_500_ERROR.md) - Detailed explanation of all changes
- [Error Investigation Guide](backend/error_investigation_guide.md) - Debugging guide for production issues
- [Test Script](backend/test_template_lookup_fix.py) - Unit tests for the fix

## Emergency Contacts

If critical issues arise:
1. Check Railway logs first
2. Review [Error Investigation Guide](backend/error_investigation_guide.md)
3. Roll back deployment if necessary
4. Document any new issues found

## Sign-Off

- [ ] Code changes reviewed and tested
- [ ] Unit tests pass
- [ ] Deployment plan reviewed
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Documentation updated

**Deployed by**: _________________
**Date**: _________________
**Deployment verified**: [ ] Yes [ ] No
**Issues found**: _________________
