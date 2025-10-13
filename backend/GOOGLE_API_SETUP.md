# Google API Setup for Forms and Sheets Integration

This document explains the Google API configuration setup for the Google Forms to Google Sheets integration feature.

## Overview

The integration allows users to:
- Connect to Google Forms and retrieve form responses
- Export form data to Google Sheets
- Schedule automatic exports
- Transform and format data during export

## Dependencies Installed

The following Python packages have been added to `requirements.txt`:

- `google-api-python-client>=2.0.0` - Core Google API client library
- `google-auth>=2.0.0` - Google authentication library
- `google-auth-oauthlib>=1.0.0` - OAuth 2.0 flow for Google APIs
- `google-auth-httplib2>=0.1.0` - HTTP transport for Google Auth

## Configuration Variables

### Added to `config.py`

```python
# Google API Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/v1/auth/google/callback')
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/forms.body.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# Google API Rate Limiting
GOOGLE_API_RATE_LIMIT = int(os.getenv('GOOGLE_API_RATE_LIMIT', 100))
GOOGLE_API_QUOTA_USER = os.getenv('GOOGLE_API_QUOTA_USER', 'default')

# Google API Retry Configuration
GOOGLE_API_MAX_RETRIES = int(os.getenv('GOOGLE_API_MAX_RETRIES', 3))
GOOGLE_API_RETRY_DELAY = int(os.getenv('GOOGLE_API_RETRY_DELAY', 1))
GOOGLE_API_BACKOFF_FACTOR = float(os.getenv('GOOGLE_API_BACKOFF_FACTOR', 2.0))

# Google API Timeout Configuration
GOOGLE_API_TIMEOUT = int(os.getenv('GOOGLE_API_TIMEOUT', 30))
GOOGLE_API_CONNECT_TIMEOUT = int(os.getenv('GOOGLE_API_CONNECT_TIMEOUT', 10))
```

### Environment Variables

Added to `.env`:

```bash
# Google Forms and Sheets Integration Configuration
GOOGLE_API_RATE_LIMIT=100
GOOGLE_API_QUOTA_USER=default
GOOGLE_API_MAX_RETRIES=3
GOOGLE_API_RETRY_DELAY=1
GOOGLE_API_BACKOFF_FACTOR=2.0
GOOGLE_API_TIMEOUT=30
GOOGLE_API_CONNECT_TIMEOUT=10
```

## Required Google API Scopes

The integration requires the following OAuth 2.0 scopes:

1. **`https://www.googleapis.com/auth/forms.responses.readonly`**
   - Read form responses from Google Forms
   - Required for fetching form submission data

2. **`https://www.googleapis.com/auth/forms.body.readonly`**
   - Read form structure and metadata
   - Required for understanding form schema and questions

3. **`https://www.googleapis.com/auth/spreadsheets`**
   - Create, read, and modify Google Sheets
   - Required for exporting data to spreadsheets

4. **`https://www.googleapis.com/auth/drive.file`**
   - Access and manage files created by the application
   - Required for sharing and managing exported sheets

## Setup Instructions

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Forms API
   - Google Sheets API
   - Google Drive API

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **"Create Credentials" > "OAuth 2.0 Client IDs"**
3. Set application type to **"Web application"**
4. Add authorized redirect URIs:
   - `http://localhost:5000/api/v1/auth/google/callback` (development)
   - Your production callback URL
5. Download the client configuration JSON file

### 3. Environment Configuration

1. Copy `.env.google-api.example` to your `.env` file
2. Fill in your actual Google API credentials:
   ```bash
   GOOGLE_CLIENT_ID=your_actual_client_id
   GOOGLE_CLIENT_SECRET=your_actual_client_secret
   ```

### 4. Optional: Service Account Setup

For server-to-server access (optional):

1. Go to **APIs & Services > Credentials**
2. Click **"Create Credentials" > "Service Account"**
3. Download the JSON key file
4. Set the path in your environment:
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
   ```

## Testing the Setup

Run the configuration test script:

```bash
cd backend
python test_google_api_config.py
```

This will verify:
- All required packages are installed
- Configuration is loaded correctly
- Environment variables are set
- Required scopes are configured

## Configuration Files Created

1. **`backend/.env.google-api.example`** - Template for environment variables
2. **`backend/test_google_api_config.py`** - Configuration test script
3. **`backend/GOOGLE_API_SETUP.md`** - This documentation file

## Next Steps

After completing this setup, you can proceed to implement:

1. Database models for integration management (Task 2)
2. OAuth Manager Service (Task 3)
3. Google Sheets Service (Task 4)
4. Enhanced Google Forms Service (Task 5)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all packages are installed with `pip install -r requirements.txt`
2. **Authentication Errors**: Verify your OAuth credentials are correct
3. **Scope Errors**: Ensure all required scopes are enabled in Google Cloud Console
4. **Rate Limiting**: Adjust `GOOGLE_API_RATE_LIMIT` if you encounter quota issues

### Testing Individual Components

```python
# Test Google Auth import
from google.auth.transport.requests import Request

# Test OAuth flow import
from google_auth_oauthlib.flow import Flow

# Test API client import
from googleapiclient.discovery import build

# Test configuration
from config import Config
print(Config.GOOGLE_SCOPES)
```

## Security Notes

- Never commit actual credentials to version control
- Use environment variables for sensitive configuration
- Regularly rotate OAuth credentials
- Monitor API usage and quotas
- Implement proper error handling for authentication failures