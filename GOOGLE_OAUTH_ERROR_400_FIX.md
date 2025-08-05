# Google OAuth Configuration Fix Guide

## Issue: Error 401: deleted_client (flowName=GeneralOAuthFlow)

This error indicates that the OAuth client ID has been deleted from the Google Cloud Console. You need to create a new OAuth client.

## Steps to Fix:

### 1. Create New OAuth Client in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project "stratosys" (or create a new project if needed)
3. Navigate to **APIs & Services** → **Credentials**
4. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
5. Select **Application type**: **Web application**
6. Give it a name like "Forms Integration Client"

### 2. Configure the New OAuth Client

**Authorized JavaScript origins:**

```
http://localhost:5173
http://localhost:5000
```

**Authorized redirect URIs:**

```
http://localhost:5000/api/google-forms/callback
```

### 3. Download the Client Configuration

1. After creating the client, click the **Download JSON** button
2. Save the file as `client_secret_[CLIENT_ID].json`
3. Copy the `client_id` and `client_secret` values

### 4. Update Backend Configuration

Update the `credentials.json` file with the new client information:

```json
{
  "web": {
    "client_id": "YOUR_NEW_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "stratosys",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_NEW_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:5000/api/google-forms/callback"]
  }
}
```

### 5. Update Environment Files

Update `.env` files with the new client ID:

**Backend `.env`:**

```
client_id=YOUR_NEW_CLIENT_ID.apps.googleusercontent.com
client_secret=YOUR_NEW_CLIENT_SECRET
```

**Frontend `.env`:**

```
VITE_GOOGLE_CLIENT_ID=YOUR_NEW_CLIENT_ID.apps.googleusercontent.com
```

### 6. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (or **Internal** if using Google Workspace)
3. Fill in required fields:
   - **App name**: "Forms Integration App"
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Add test users in the **Test users** section:
   - Add: `firebts5k@gmail.com`

### 7. Enable Required APIs

Make sure these APIs are enabled in **APIs & Services** → **Library**:

- **Google Forms API**
- **Google Drive API**

### 8. Update Project Files

After getting the new client credentials, you'll need to update several files:

1. **Update `backend/credentials.json`** with new client info
2. **Update `backend/.env`** with new client_id and client_secret
3. **Update `frontend/.env`** with new VITE_GOOGLE_CLIENT_ID
4. **Clear any existing tokens** in `backend/tokens/` directory

### 9. Restart Services

After making all changes:

1. Restart backend server
2. Restart frontend development server
3. Clear browser cookies/cache
4. Try the Google Forms authentication again

## Quick Fix Command

Once you have the new credentials, you can run these commands to update the configuration:

```bash
# Update backend credentials.json
# Replace YOUR_NEW_CLIENT_ID and YOUR_NEW_CLIENT_SECRET with actual values

# Clear existing tokens
rm -rf backend/tokens/*

# Restart backend
cd backend && python run.py
```

## Troubleshooting

If you still get the error:

1. Check if the OAuth client type is "Web application"
2. Verify the redirect URI exactly matches: `http://localhost:5000/api/google-forms/callback`
3. Ensure the email is added as a test user
4. Try clearing browser cookies/cache
5. Check backend logs for detailed error information

## Testing

After fixing:

1. Restart backend server
2. Try the Google Forms authentication again
3. Check backend logs for detailed error information
