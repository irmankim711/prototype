# StratoSys API - Postman Collection

Complete Postman collection for testing the StratoSys API (Form Builder & Report Generator Platform).

## Files

- `StratoSys_API.postman_collection.json` - Main API collection with all endpoints
- `StratoSys_Local.postman_environment.json` - Local development environment
- `StratoSys_Production.postman_environment.json` - Production environment (Railway)

## Quick Start

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button
3. Select all three JSON files from the `postman/` directory
4. Click **Import**

### 2. Select Environment

1. In the top-right corner of Postman, select the environment:
   - **StratoSys - Local Development** for local testing
   - **StratoSys - Production (Railway)** for production testing

### 3. Configure Firebase Token

Before making authenticated requests, you need to obtain a Firebase ID token:

#### Option A: Use Token Extractor Tool (Easiest Method)

1. Open your StratoSys frontend and log in with your Firebase account
2. Open `postman/get-firebase-token.html` in your browser
3. Click **Extract Token** button
4. The token will be automatically found and displayed with detailed information
5. Click **Copy to Clipboard** button
6. In Postman:
   - Click on **Environments** (left sidebar)
   - Select your active environment
   - Paste the token into the `firebase_token` variable
   - Click **Save**

The HTML tool will:
- Automatically search for your Firebase token in localStorage/sessionStorage
- Display token expiration time with live countdown
- Show decoded token information (user ID, email, etc.)
- Warn you if the token is expired or expiring soon

#### Option B: Get Token from Browser DevTools

1. Open your StratoSys frontend in a browser
2. Log in with your Firebase account
3. Open DevTools (F12)
4. Go to **Application** tab → **Local Storage** → Select your domain
5. Look for key named `firebaseToken` or `accessToken`
6. Copy the value
7. In Postman:
   - Click on **Environments** (left sidebar)
   - Select your active environment
   - Paste the token into the `firebase_token` variable
   - Click **Save**

#### Option C: Get Token from Console (Alternative)

If your app exposes the auth object, you can try:

```javascript
// In browser console after logging in
localStorage.getItem('firebaseToken')
```

Copy the output (without quotes) to Postman.

**Note:** Firebase ID tokens expire after 1 hour. You'll need to refresh the token periodically. The Token Extractor tool shows you exactly when your token will expire.

### 4. Test the API

1. Start with **Health & Status** folder to verify API is running
2. Try **Authentication > Firebase Sync/Login** to test authentication
3. Explore other endpoints

## Collection Structure

### 1. Authentication
- Firebase login/sync
- Token verification
- User profile management
- Logout

### 2. Forms
- CRUD operations for forms
- Form submissions (public and authenticated)
- QR code generation
- Field type discovery

### 3. Reports
- Report generation
- Download reports
- Report templates
- Automated reporting

### 4. Excel Export
- Export form submissions to Excel
- Async export with status tracking
- Export history
- Bulk export

### 5. Google Forms Integration
- Connect Google Forms
- Fetch form data
- Generate reports from Google Forms
- Export to Excel

### 6. Analytics
- Dashboard statistics
- Trends and insights
- Form performance metrics
- Real-time analytics

### 7. Dashboard
- Summary metrics
- Recent items
- Performance data

### 8. Health & Status
- API health checks
- Database status
- System information
- **No authentication required**

### 9. User Management
- Profile management
- Avatar upload
- Password change
- Account deletion

### 10. NextGen Report Builder
- Data source management
- Template operations
- Report generation with advanced features

### 11. File Management
- File uploads
- List files
- Storage statistics

## Authentication

Most endpoints require Firebase authentication. The collection uses **Bearer Token** authentication at the collection level.

### Setting Authentication

The `firebase_token` variable is automatically used in the `Authorization` header:

```
Authorization: Bearer {{firebase_token}}
```

Endpoints that **don't require authentication**:
- All endpoints in **Health & Status** folder
- `Submit Form (Public)` - for public form submissions
- `API Root` - basic API information

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `base_url` | API base URL | `http://localhost:5000` or `https://your-app.railway.app` |
| `firebase_token` | Firebase ID token | Auto-set after authentication |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `form_id` | Form ID for testing | `1` |
| `report_id` | Report ID for testing | `1` |
| `google_form_id` | Google Form ID | Empty |
| `template_id` | Report template ID | `1` |
| `user_id` | User ID | Empty |
| `export_id` | Export task ID | Empty |

These variables are used in request URLs like:
- `{{base_url}}/api/forms/{{form_id}}`
- `{{base_url}}/api/reports/{{report_id}}/download`

## Common Request Examples

### Create a Form

```json
POST {{base_url}}/api/forms/

{
  "title": "Customer Feedback Form",
  "description": "Please share your feedback",
  "fields": [
    {
      "name": "full_name",
      "type": "text",
      "label": "Full Name",
      "required": true
    },
    {
      "name": "email",
      "type": "email",
      "label": "Email Address",
      "required": true
    },
    {
      "name": "rating",
      "type": "rating",
      "label": "Rate your experience",
      "required": true
    }
  ],
  "is_public": true,
  "is_active": true
}
```

### Submit a Form (Public)

```json
POST {{base_url}}/api/forms/{{form_id}}/submissions

{
  "data": {
    "full_name": "Jane Smith",
    "email": "jane@example.com",
    "rating": 5
  }
}
```

### Export to Excel

```json
POST {{base_url}}/api/forms/{{form_id}}/export-excel

{
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "include_metadata": true,
  "max_records": 10000
}
```

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    // Response data
  }
}
```

### Error Response

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

## Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_AUTH_HEADER` | Authorization header not provided |
| `INVALID_AUTH_HEADER` | Invalid Authorization header format |
| `INVALID_TOKEN` | Token is invalid or expired |
| `TOKEN_VERIFICATION_FAILED` | Token verification error |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `AUTH_SERVICE_UNAVAILABLE` | Firebase service unavailable |
| `USER_NOT_FOUND` | User account not found |
| `FORM_NOT_FOUND` | Form not found |
| `INTERNAL_ERROR` | Server error |

## Rate Limits

Be aware of rate limits on certain endpoints:

| Endpoint | Limit |
|----------|-------|
| Firebase login | 10/minute |
| Firebase registration | 5/hour |
| Excel export (per form) | 20/hour |
| Bulk export | 10/hour |
| Token verification | 20/minute |

## CORS Configuration

The API supports CORS for the following origins:

- `http://localhost:3000`
- `http://localhost:5173`
- `http://localhost:5174`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`
- `http://127.0.0.1:5174`
- `https://stratosys-irmankim711s-projects.vercel.app`
- `https://*.vercel.app` (all Vercel deployments)

## Testing Workflow

### 1. Initial Setup

```
1. Health Check → Verify API is running
2. Firebase Sync/Login → Authenticate and get user data
3. Verify Token → Confirm token is valid
```

### 2. Form Testing

```
1. Get Field Types → See available field types
2. Create Form → Create a test form
3. Get All Forms → Verify form was created
4. Submit Form (Public) → Submit test data
5. Get Form Submissions → View submitted data
6. Generate QR Code → Create QR code for form
```

### 3. Export Testing

```
1. Export Form to Excel → Start export
2. Get Export Status → Check export progress
3. Download Excel File → Download completed export
4. Get Export History → View export history
```

### 4. Report Testing

```
1. Get Report Templates → View available templates
2. Create Report → Generate a report
3. Get Report by ID → View report details
4. Download Report → Download generated report
```

### 5. Analytics Testing

```
1. Get Dashboard Stats → View overall statistics
2. Get Analytics Trends → View trend data
3. Get Top Forms → See best performing forms
4. Get Real-time Analytics → View real-time data
```

## Troubleshooting

### Token Expired Error

**Error:** `INVALID_TOKEN` or `Token is invalid or expired`

**Solution:**
1. Get a fresh Firebase token (see Step 3 above)
2. Update the `firebase_token` environment variable
3. Retry the request

### CORS Error

**Error:** CORS policy blocking request

**Solution:**
1. Ensure you're using an allowed origin
2. Check that the API has proper CORS configuration
3. For local development, use `localhost` URLs exactly as configured

### 404 Not Found

**Error:** `Cannot GET /api/endpoint`

**Solution:**
1. Verify the API is running
2. Check the `base_url` in your environment
3. Ensure the endpoint path is correct

### Rate Limit Exceeded

**Error:** `429 Too Many Requests`

**Solution:**
1. Wait for the rate limit window to reset
2. Reduce request frequency
3. Check rate limits table above

## Tips

1. **Use Collection Variables**: The collection has variables for common IDs (`form_id`, `report_id`, etc.). Update these instead of hardcoding values.

2. **Test Scripts**: Add test scripts to requests to automatically validate responses and set variables:

```javascript
// Example: Save form_id from response
pm.test("Status is 200", () => {
    pm.response.to.have.status(200);
});

const response = pm.response.json();
pm.environment.set("form_id", response.data.id);
```

3. **Pre-request Scripts**: Automatically refresh tokens or set dynamic values:

```javascript
// Example: Set timestamp
pm.environment.set("timestamp", new Date().toISOString());
```

4. **Organize Tests**: Use folders to group related tests and run them sequentially using Collection Runner.

5. **Save Responses**: Use **Save Response** to create example responses for documentation.

## Support

For issues or questions:
1. Check API documentation
2. Review error messages and codes
3. Verify authentication token is valid
4. Ensure environment variables are set correctly

## Version History

- **v1.0** - Initial collection with all major endpoints
  - Authentication
  - Forms CRUD
  - Reports & Templates
  - Excel Export
  - Google Forms Integration
  - Analytics
  - Dashboard
  - Health Checks
  - User Management
  - NextGen Report Builder
  - File Management
