# POSTMAN API TEST CASES

## Overview
Comprehensive test cases for API testing using Postman.

**Total Test Cases**: 85+
**Base URL**: `http://localhost:5000` or your deployed URL
**Authentication**: Firebase ID Token (Bearer)

---

## Quick Reference

| Category | Test Cases | Priority |
|----------|-----------|----------|
| Authentication | 8 | HIGH |
| User Management | 8 | HIGH |
| Forms Management | 10 | HIGH |
| Google Forms Integration | 6 | MEDIUM |
| Reports Management | 15 | HIGH |
| Analytics & Dashboard | 8 | MEDIUM |
| Excel & Export | 5 | MEDIUM |
| CSRF Protection | 3 | LOW |
| Health & Status | 4 | LOW |
| Error Handling | 10 | HIGH |
| **TOTAL** | **77** | - |

---

## Postman Setup

### Environment Variables
```json
{
  "base_url": "http://localhost:5000",
  "firebase_token": "",
  "user_id": "",
  "form_id": "",
  "report_id": "",
  "csrf_token": ""
}
```

### Global Headers
```
Authorization: Bearer {{firebase_token}}
Content-Type: application/json
```

---

## 1. AUTHENTICATION TESTS (8 Test Cases)

### TC-AUTH-001: Firebase Config Validation
- **Endpoint**: `POST /api/firebase-config-validation`
- **Method**: POST
- **Auth**: None
- **Body**:
```json
{
  "apiKey": "your-api-key",
  "authDomain": "project.firebaseapp.com",
  "projectId": "project-id"
}
```
- **Expected**: 200 OK, `{valid: true}`
- **Assertions**:
  - Status code is 200
  - Response contains `valid: true`

---

### TC-AUTH-002: Login with Valid Token
- **Endpoint**: `POST /api/firebase-login`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**: `{idToken: "{{firebase_token}}"}`
- **Expected**: 200 OK with user data
- **Assertions**:
  - Status code is 200
  - Response has `uid`, `email`
  - Save `uid` to environment

---

### TC-AUTH-003: Login with Invalid Token
- **Endpoint**: `POST /api/firebase-login`
- **Method**: POST
- **Auth**: Invalid Token
- **Expected**: 401 Unauthorized
- **Assertions**:
  - Status code is 401
  - Error message present

---

### TC-AUTH-004: Get Current User Profile
- **Endpoint**: `GET /api/users/profile`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK with profile
- **Assertions**:
  - Status code is 200
  - Profile data returned

---

### TC-AUTH-005: Logout User
- **Endpoint**: `POST /api/firebase-logout`
- **Method**: POST
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Success message returned

---

### TC-AUTH-006: Access Protected Route Without Auth
- **Endpoint**: `GET /api/forms`
- **Method**: GET
- **Auth**: None
- **Expected**: 401 Unauthorized
- **Assertions**:
  - Status code is 401

---

### TC-AUTH-007: Firebase Sync Status
- **Endpoint**: `POST /api/firebase-sync-status`
- **Method**: POST
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Sync status returned

---

### TC-AUTH-008: Rate Limit Test
- **Endpoint**: `POST /api/firebase-sync-status`
- **Method**: POST
- **Auth**: Bearer Token
- **Iterations**: 35 rapid requests
- **Expected**: 429 after 30 requests
- **Assertions**:
  - First 30 return 200
  - 31st returns 429

---

## 2. USER MANAGEMENT TESTS (8 Test Cases)

### TC-USER-001: Get User Profile
- **Endpoint**: `GET /api/users/profile`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK with full profile
- **Assertions**:
  - All fields present (uid, email, displayName, etc.)

---

### TC-USER-002: Update User Profile
- **Endpoint**: `PUT /api/users/profile`
- **Method**: PUT
- **Auth**: Bearer Token
- **Body**:
```json
{
  "displayName": "Updated Name",
  "phoneNumber": "+1234567890"
}
```
- **Expected**: 200 OK
- **Assertions**:
  - Fields updated successfully

---

### TC-USER-003: Change Password
- **Endpoint**: `POST /api/users/change-password`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**:
```json
{
  "currentPassword": "old123",
  "newPassword": "new456"
}
```
- **Expected**: 200 OK
- **Assertions**:
  - Success message

---

### TC-USER-004: Get User Settings
- **Endpoint**: `GET /api/users/settings`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK with settings
- **Assertions**:
  - Settings object returned

---

### TC-USER-005: Update Settings
- **Endpoint**: `PUT /api/users/settings`
- **Method**: PUT
- **Auth**: Bearer Token
- **Body**:
```json
{
  "theme": "dark",
  "language": "en"
}
```
- **Expected**: 200 OK
- **Assertions**:
  - Settings updated

---

### TC-USER-006: Admin - Get All Users
- **Endpoint**: `GET /api/users`
- **Method**: GET
- **Auth**: Bearer Token (Admin)
- **Query**: `?page=1&limit=10`
- **Expected**: 200 OK with user list
- **Assertions**:
  - Pagination data present

---

### TC-USER-007: Admin - Update User Role
- **Endpoint**: `PUT /api/users/:userId/role`
- **Method**: PUT
- **Auth**: Bearer Token (Admin)
- **Body**: `{role: "admin"}`
- **Expected**: 200 OK
- **Assertions**:
  - Role updated

---

### TC-USER-008: Non-Admin Access Denied
- **Endpoint**: `GET /api/users`
- **Method**: GET
- **Auth**: Bearer Token (Non-Admin)
- **Expected**: 403 Forbidden
- **Assertions**:
  - Permission denied

---

## 3. FORMS MANAGEMENT TESTS (10 Test Cases)

### TC-FORM-001: Create New Form
- **Endpoint**: `POST /api/forms`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**:
```json
{
  "title": "Customer Feedback",
  "description": "Collect feedback",
  "fields": [
    {"type": "text", "label": "Name", "required": true},
    {"type": "email", "label": "Email", "required": true}
  ]
}
```
- **Expected**: 201 Created
- **Assertions**:
  - Form ID returned
  - Save to environment

---

### TC-FORM-002: Get All Forms
- **Endpoint**: `GET /api/forms`
- **Method**: GET
- **Auth**: Bearer Token
- **Query**: `?page=1&limit=10`
- **Expected**: 200 OK
- **Assertions**:
  - Forms array returned

---

### TC-FORM-003: Get Form by ID
- **Endpoint**: `GET /api/forms/:id`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Correct form returned

---

### TC-FORM-004: Update Form
- **Endpoint**: `PUT /api/forms/:id`
- **Method**: PUT
- **Auth**: Bearer Token
- **Body**:
```json
{
  "title": "Updated Title",
  "status": "active"
}
```
- **Expected**: 200 OK
- **Assertions**:
  - Form updated

---

### TC-FORM-005: Delete Form
- **Endpoint**: `DELETE /api/forms/:id`
- **Method**: DELETE
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Success message

---

### TC-FORM-006: Get Form Statistics
- **Endpoint**: `GET /api/forms/:id/statistics`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Stats data returned

---

### TC-FORM-007: Toggle Form Property
- **Endpoint**: `PATCH /api/forms/:id/toggle`
- **Method**: PATCH
- **Auth**: Bearer Token
- **Body**: `{property: "isPublic", value: true}`
- **Expected**: 200 OK
- **Assertions**:
  - Property toggled

---

### TC-FORM-008: Submit Form Response
- **Endpoint**: `POST /api/forms/:id/submit`
- **Method**: POST
- **Auth**: None (public form)
- **Body**:
```json
{
  "responses": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```
- **Expected**: 201 Created
- **Assertions**:
  - Submission ID returned

---

### TC-FORM-009: Get Form Responses
- **Endpoint**: `GET /api/forms/:id/responses`
- **Method**: GET
- **Auth**: Bearer Token
- **Query**: `?page=1&limit=20`
- **Expected**: 200 OK
- **Assertions**:
  - Responses array returned

---

### TC-FORM-010: Export Form Responses
- **Endpoint**: `GET /api/forms/:id/export`
- **Method**: GET
- **Auth**: Bearer Token
- **Query**: `?format=csv`
- **Expected**: 200 OK
- **Assertions**:
  - CSV file downloaded

---

## 4. GOOGLE FORMS INTEGRATION TESTS (6 Test Cases)

### TC-GFORM-001: OAuth Callback
- **Endpoint**: `GET /api/google-forms/callback`
- **Method**: GET
- **Query**: `?code=auth_code&state=state`
- **Expected**: 302 Redirect
- **Assertions**:
  - Redirects with token

---

### TC-GFORM-002: Get Google Forms List
- **Endpoint**: `GET /api/google-forms/forms`
- **Method**: GET
- **Auth**: Bearer Token + Google OAuth
- **Expected**: 200 OK
- **Assertions**:
  - Forms array returned

---

### TC-GFORM-003: Get Form Responses
- **Endpoint**: `GET /api/google-forms/forms/:formId/responses`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Responses returned

---

### TC-GFORM-004: Generate Analytics
- **Endpoint**: `POST /api/google-forms/analytics`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**: `{formId: "abc123"}`
- **Expected**: 200 OK
- **Assertions**:
  - Analytics data returned

---

### TC-GFORM-005: Sync Status
- **Endpoint**: `GET /api/google-forms/status`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Connection status returned

---

### TC-GFORM-006: Disconnect Google Account
- **Endpoint**: `POST /api/google-forms/disconnect`
- **Method**: POST
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Successfully disconnected

---

## 5. REPORTS MANAGEMENT TESTS (15 Test Cases)

### TC-REPORT-001: Create Report
- **Endpoint**: `POST /api/reports`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**:
```json
{
  "title": "Sales Report",
  "formId": 123,
  "chartType": "bar",
  "dateRange": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  }
}
```
- **Expected**: 201 Created
- **Assertions**:
  - Report ID returned

---

### TC-REPORT-002: Get All Reports
- **Endpoint**: `GET /api/reports`
- **Method**: GET
- **Auth**: Bearer Token
- **Query**: `?page=1&limit=10`
- **Expected**: 200 OK
- **Assertions**:
  - Reports array returned

---

### TC-REPORT-003: Get Report by ID
- **Endpoint**: `GET /api/reports/:id`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Complete report data

---

### TC-REPORT-004: Update Report
- **Endpoint**: `PUT /api/reports/:id`
- **Method**: PUT
- **Auth**: Bearer Token
- **Body**: `{title: "Updated Report"}`
- **Expected**: 200 OK
- **Assertions**:
  - Report updated

---

### TC-REPORT-005: Delete Report
- **Endpoint**: `DELETE /api/reports/:id`
- **Method**: DELETE
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Success message

---

### TC-REPORT-006: Export as PDF
- **Endpoint**: `GET /api/reports/:id/export/pdf`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK (PDF)
- **Assertions**:
  - Content-Type is PDF

---

### TC-REPORT-007: Export as Excel
- **Endpoint**: `GET /api/reports/:id/export/xlsx`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK (Excel)
- **Assertions**:
  - Content-Type is Excel

---

### TC-REPORT-008: Export as Word
- **Endpoint**: `GET /api/reports/:id/export/docx`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK (Word)
- **Assertions**:
  - Content-Type is DOCX

---

### TC-REPORT-009: Get Generation Status
- **Endpoint**: `GET /api/reports/:id/status`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Status and progress returned

---

### TC-REPORT-010: AI Enhance Report
- **Endpoint**: `POST /api/reports/:id/enhance`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**: `{enhancements: ["insights"]}`
- **Expected**: 200 OK
- **Assertions**:
  - Enhanced data returned

---

### TC-REPORT-011: Get Report Preview
- **Endpoint**: `GET /api/reports/:id/preview`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Preview data with reportId at top level

---

### TC-REPORT-012: Clone Report
- **Endpoint**: `POST /api/reports/:id/clone`
- **Method**: POST
- **Auth**: Bearer Token
- **Expected**: 201 Created
- **Assertions**:
  - New report ID returned

---

### TC-REPORT-013: Get Report History
- **Endpoint**: `GET /api/reports/:id/history`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Version history returned

---

### TC-REPORT-014: Share Report
- **Endpoint**: `POST /api/reports/:id/share`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**: `{email: "user@example.com"}`
- **Expected**: 200 OK
- **Assertions**:
  - Share link generated

---

### TC-REPORT-015: Rate Limit Test
- **Endpoint**: `POST /api/reports`
- **Iterations**: 25 requests
- **Expected**: 429 after limit
- **Assertions**:
  - Rate limit enforced

---

## 6. ANALYTICS & DASHBOARD TESTS (8 Test Cases)

### TC-ANALYTICS-001: Dashboard Overview
- **Endpoint**: `GET /api/analytics/dashboard`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - All metrics returned

---

### TC-ANALYTICS-002: Submission Trends
- **Endpoint**: `GET /api/analytics/submissions/trends`
- **Method**: GET
- **Auth**: Bearer Token
- **Query**: `?period=7d`
- **Expected**: 200 OK
- **Assertions**:
  - Trends data returned

---

### TC-ANALYTICS-003: Geographic Distribution
- **Endpoint**: `GET /api/analytics/geography`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Geographic data returned

---

### TC-ANALYTICS-004: Performance Comparison
- **Endpoint**: `GET /api/analytics/performance`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Performance metrics returned

---

### TC-ANALYTICS-005: Time Distribution
- **Endpoint**: `GET /api/analytics/time-distribution`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Hourly distribution returned

---

### TC-ANALYTICS-006: Custom Chart Data
- **Endpoint**: `POST /api/analytics/custom-chart`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**:
```json
{
  "formId": 123,
  "chartType": "pie",
  "field": "category"
}
```
- **Expected**: 200 OK
- **Assertions**:
  - Chart data returned

---

### TC-ANALYTICS-007: Real-time Metrics
- **Endpoint**: `GET /api/analytics/realtime`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Live metrics returned

---

### TC-ANALYTICS-008: Export Analytics
- **Endpoint**: `GET /api/analytics/export`
- **Method**: GET
- **Auth**: Bearer Token
- **Query**: `?format=csv`
- **Expected**: 200 OK
- **Assertions**:
  - CSV downloaded

---

## 7. EXCEL & EXPORT TESTS (5 Test Cases)

### TC-EXCEL-001: AI Generate Excel
- **Endpoint**: `POST /api/ai-excel/generate`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**: `{prompt: "Create sales report"}`
- **Expected**: 202 Accepted
- **Assertions**:
  - Task ID returned

---

### TC-EXCEL-002: Get Generation Status
- **Endpoint**: `GET /api/ai-excel/status/:taskId`
- **Method**: GET
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Status returned

---

### TC-EXCEL-003: Export Form to Excel
- **Endpoint**: `POST /api/forms/:id/export/excel`
- **Method**: POST
- **Auth**: Bearer Token
- **Expected**: 200 OK
- **Assertions**:
  - Excel file downloaded

---

### TC-EXCEL-004: Excel Service Health
- **Endpoint**: `GET /api/ai-excel/health`
- **Method**: GET
- **Auth**: None
- **Expected**: 200 OK
- **Assertions**:
  - Service healthy

---

### TC-EXCEL-005: Bulk Export
- **Endpoint**: `POST /api/export/bulk`
- **Method**: POST
- **Auth**: Bearer Token
- **Body**: `{formIds: [1, 2, 3]}`
- **Expected**: 202 Accepted
- **Assertions**:
  - Batch job created

---

## 8. CSRF PROTECTION TESTS (3 Test Cases)

### TC-CSRF-001: Generate Token
- **Endpoint**: `GET /api/csrf-token`
- **Method**: GET
- **Auth**: None
- **Expected**: 200 OK
- **Assertions**:
  - Token returned

---

### TC-CSRF-002: Validate Token
- **Endpoint**: `POST /api/csrf-validate`
- **Method**: POST
- **Body**: `{csrfToken: "token"}`
- **Expected**: 200 OK
- **Assertions**:
  - Valid response

---

### TC-CSRF-003: Invalid Token
- **Endpoint**: `POST /api/csrf-validate`
- **Method**: POST
- **Body**: `{csrfToken: "invalid"}`
- **Expected**: 400 Bad Request
- **Assertions**:
  - Error returned

---

## 9. HEALTH & STATUS TESTS (4 Test Cases)

### TC-HEALTH-001: API Health
- **Endpoint**: `GET /health`
- **Method**: GET
- **Auth**: None
- **Expected**: 200 OK
- **Assertions**:
  - Status is healthy

---

### TC-HEALTH-002: Database Health
- **Endpoint**: `GET /health/db`
- **Method**: GET
- **Auth**: None
- **Expected**: 200 OK
- **Assertions**:
  - DB connected

---

### TC-HEALTH-003: Production Health
- **Endpoint**: `GET /api/production/health`
- **Method**: GET
- **Auth**: None
- **Expected**: 200 OK
- **Assertions**:
  - All services up

---

### TC-HEALTH-004: Redis Health
- **Endpoint**: `GET /health/redis`
- **Method**: GET
- **Auth**: None
- **Expected**: 200 OK
- **Assertions**:
  - Redis connected

---

## 10. ERROR HANDLING TESTS (10 Test Cases)

### TC-ERROR-001: 404 Not Found
- **Endpoint**: `GET /api/invalid`
- **Expected**: 404
- **Assertions**: Error message

---

### TC-ERROR-002: Malformed JSON
- **Endpoint**: `POST /api/forms`
- **Body**: Invalid JSON
- **Expected**: 400
- **Assertions**: Format error

---

### TC-ERROR-003: Missing Fields
- **Endpoint**: `POST /api/forms`
- **Body**: `{description: "missing title"}`
- **Expected**: 400
- **Assertions**: Validation errors

---

### TC-ERROR-004: Resource Not Found
- **Endpoint**: `GET /api/forms/99999`
- **Expected**: 404
- **Assertions**: Not found

---

### TC-ERROR-005: Server Error
- **Endpoint**: `GET /api/test/error`
- **Expected**: 500
- **Assertions**: Error message

---

### TC-ERROR-006: Unauthorized Access
- **Endpoint**: `DELETE /api/forms/:id` (wrong user)
- **Expected**: 403
- **Assertions**: Permission denied

---

### TC-ERROR-007: Timeout
- **Endpoint**: Long-running operation
- **Expected**: 504
- **Assertions**: Timeout message

---

### TC-ERROR-008: Conflict
- **Endpoint**: Concurrent updates
- **Expected**: 409
- **Assertions**: Conflict detected

---

### TC-ERROR-009: Invalid Parameters
- **Endpoint**: `GET /api/forms?page=invalid`
- **Expected**: 400
- **Assertions**: Parameter error

---

### TC-ERROR-010: File Too Large
- **Endpoint**: `POST /api/upload`
- **Body**: Large file
- **Expected**: 413
- **Assertions**: Size limit exceeded

---

## Execution Guidelines

1. **Sequential Execution**: Run tests in order
2. **Save Variables**: Store IDs in environment
3. **Clean Up**: Delete test data after
4. **Monitor Limits**: Respect rate limits
5. **Response Times**: Track performance
6. **Schema Validation**: Validate responses

---

**Total Test Cases**: 77
**Estimated Execution Time**: 45-60 minutes
**Coverage**: Core API functionality
