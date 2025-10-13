# Google Forms Integration Setup Guide

## Prerequisites

1. Google Cloud Console account
2. Google Forms API enabled
3. OAuth 2.0 credentials configured

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Google Forms API
   - Google Drive API
   - Google Sheets API

## Step 2: Create OAuth 2.0 Credentials

1. Go to "Credentials" in Google Cloud Console
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://localhost:5000/auth/google/callback`
   - `http://localhost:5173/auth/google/callback`
5. Download the credentials JSON file

## Step 3: Configure Backend

Add to `backend/.env`:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# Google API Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

## Step 4: Configure Frontend

Add to `frontend/.env`:

```bash
# Google OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your_client_id_here
```

## Step 5: Test Integration

1. Start both backend and frontend
2. Navigate to the Google Forms section
3. Click "Connect to Google Forms"
4. Complete OAuth flow
5. You should see your Google Forms listed

## Troubleshooting

### Common Issues:

1. **"OAuth client not found"**
   - Check client ID is correct
   - Ensure redirect URIs match exactly

2. **"Access denied"**
   - Check API permissions
   - Verify OAuth consent screen is configured

3. **"Forms not loading"**
   - Check API quotas
   - Verify Forms API is enabled

### Testing Commands:

```bash
# Test Google Forms API connectivity
python test-google-forms-api.py

# Check OAuth configuration
python check-oauth-config.py
```

## API Endpoints

Once configured, these endpoints will work:

- `GET /api/google-forms/status` - Check integration status
- `GET /api/google-forms/forms` - List user's forms
- `GET /api/google-forms/forms/{id}/responses` - Get form responses
- `POST /api/google-forms/forms/{id}/generate-report` - Generate report

## Security Notes

1. Never commit credentials to version control
2. Use environment variables for all secrets
3. Regularly rotate OAuth credentials
4. Monitor API usage and quotas