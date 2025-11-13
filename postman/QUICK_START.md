# StratoSys API - Quick Start Guide

Get up and running with Postman testing in 5 minutes.

## Step 1: Import to Postman (30 seconds)

1. Open Postman
2. Click **Import** button (top-left)
3. Drag and drop these files:
   - `StratoSys_API.postman_collection.json`
   - `StratoSys_Local.postman_environment.json`
   - `StratoSys_Production.postman_environment.json`
4. Click **Import**

## Step 2: Select Environment (5 seconds)

In the top-right corner of Postman:
- Select **StratoSys - Local Development** for local testing
- Or **StratoSys - Production (Railway)** for production

## Step 3: Get Your Firebase Token (1 minute)

### Easiest Method - Use the Token Extractor Tool

1. Log in to your StratoSys app
2. Open `get-firebase-token.html` in your browser (double-click the file)
3. Click **Extract Token**
4. Click **Copy to Clipboard**

### Alternative - Use Browser DevTools

1. Log in to your StratoSys app
2. Press F12 to open DevTools
3. Go to: **Application** → **Local Storage** → your domain
4. Find `firebaseToken` and copy its value

## Step 4: Add Token to Postman (30 seconds)

1. In Postman, click **Environments** in the left sidebar
2. Select **StratoSys - Local Development**
3. Find the `firebase_token` variable
4. Paste your copied token in the **CURRENT VALUE** column
5. Click **Save** (Ctrl+S)

## Step 5: Test Your Setup (1 minute)

### Test 1: Health Check (No Auth)
```
GET {{base_url}}/api/health
```
Expected: `200 OK` with status information

### Test 2: Firebase Login (With Auth)
```
POST {{base_url}}/auth/firebase/firebase-sync
```
Expected: `200 OK` with user information

### Test 3: Get Your Profile
```
GET {{base_url}}/auth/firebase/profile
```
Expected: `200 OK` with your profile data

## Common Endpoints to Try

### Forms
- **Create Form**: `POST /api/forms/`
- **Get Forms**: `GET /api/forms/`
- **Submit Form**: `POST /api/forms/{{form_id}}/submissions`

### Reports
- **Create Report**: `POST /api/reports`
- **Get Reports**: `GET /api/reports`
- **Download Report**: `GET /api/reports/{{report_id}}/download`

### Excel Export
- **Export to Excel**: `POST /api/forms/{{form_id}}/export-excel`
- **Download Excel**: `GET /api/forms/{{form_id}}/download-excel`

### Analytics
- **Dashboard Stats**: `GET /api/analytics/dashboard/stats`
- **Trends**: `GET /api/analytics/trends`

## Troubleshooting

### Error: 401 Unauthorized
**Cause**: Token is missing or expired
**Fix**: Get a fresh token (Step 3) and update Postman (Step 4)

### Error: Cannot connect to server
**Cause**: Backend server is not running
**Fix**: Start your backend server on port 5000 (or update `base_url`)

### Error: CORS policy blocking
**Cause**: Request from unauthorized origin
**Fix**: The backend should allow Postman requests. Check CORS settings.

### Token expires too quickly
**Cause**: Firebase tokens expire after 1 hour
**Fix**: Refresh your token using the Token Extractor tool before making requests

## Tips

1. **Use Variables**: The collection uses `{{form_id}}`, `{{report_id}}`, etc. Update these in your environment for quick testing.

2. **Save Responses**: When you create a form/report, copy the ID from the response and save it to your environment variables.

3. **Collection Runner**: Use Postman's Collection Runner to run multiple requests in sequence.

4. **Test Scripts**: Add test scripts to automatically validate responses:
   ```javascript
   pm.test("Status is 200", () => {
       pm.response.to.have.status(200);
   });
   ```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `base_url` | `http://localhost:5000` | API base URL |
| `firebase_token` | Empty | Your Firebase ID token (add this!) |
| `form_id` | `1` | Form ID for testing |
| `report_id` | `1` | Report ID for testing |
| `google_form_id` | Empty | Google Form ID |
| `template_id` | `1` | Report template ID |

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check the API endpoint reference
- Explore the collection folders
- Set up automated tests
- Use Collection Runner for workflow testing

## Support

Need help? Check:
- [Full Documentation](README.md)
- API error messages
- Token expiration status
- Server logs

---

**Ready to test!** Start with the Health & Status folder and work your way through the collection.