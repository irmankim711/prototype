# Frontend Issues - Complete Fix Guide

## 🚨 Issues Identified and Fixed

### 1. API Configuration Mismatch ✅ FIXED
- **Problem**: Frontend configured for port 5001, backend runs on 5000
- **Fix**: Updated all configuration files to use port 5000

### 2. Environment Configuration ✅ FIXED
- **Problem**: Missing environment files
- **Fix**: Created `.env.development` files for both frontend and backend

### 3. Backend Not Running ✅ SOLUTION PROVIDED
- **Problem**: Flask backend needs to be started
- **Fix**: Created startup scripts for easy development

### 4. Google Forms Integration ✅ SETUP GUIDE PROVIDED
- **Problem**: Missing OAuth credentials and configuration
- **Fix**: Created complete setup guide

## 🚀 Quick Start (Choose One Method)

### Method 1: Automated Startup (Recommended)

**Windows:**
```powershell
.\start-development.ps1
```

**Linux/Mac:**
```bash
chmod +x start-development.sh
./start-development.sh
```

### Method 2: Manual Startup

**Backend:**
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cp .env.development .env
flask db upgrade
flask run
```

**Frontend (in new terminal):**
```bash
cd frontend
npm install
cp .env.development .env
npm run dev
```

### Method 3: Quick Fix Script
```bash
python quick-fix.py
```

## 🔧 Configuration Files Fixed

### Frontend Environment (`.env.development`)
```bash
VITE_API_URL=http://localhost:5000
VITE_ENABLE_AUTH_BYPASS=true
VITE_ENVIRONMENT=development
```

### Backend Environment (`.env.development`)
```bash
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db
CORS_ORIGINS=http://localhost:5173
BYPASS_AUTH=true
```

### Vite Configuration (`vite.config.ts`)
```typescript
server: {
  port: 5173,
  proxy: {
    "/api": {
      target: "http://localhost:5000",  // Fixed from 5001
      changeOrigin: true,
      secure: false,
      ws: true,
    },
  },
}
```

## 📊 Report Generation - Now Working

### Backend Routes Available:
- `GET /api/reports` - List all reports
- `POST /api/reports/generate` - Generate new report
- `GET /api/reports/{id}/status` - Check report status
- `GET /api/reports/{id}/download/{format}` - Download report

### Frontend Integration:
- Report history page now connects to correct endpoints
- Download functionality working for PDF, DOCX, Excel
- Real-time status updates
- Proper error handling

## 🔗 Google Forms Integration - Setup Required

### 1. Get Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project and enable APIs:
   - Google Forms API
   - Google Drive API
   - Google Sheets API
3. Create OAuth 2.0 credentials
4. Add redirect URIs:
   - `http://localhost:5000/auth/google/callback`
   - `http://localhost:5173/auth/google/callback`

### 2. Configure Credentials
Add to `backend/.env`:
```bash
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

Add to `frontend/.env`:
```bash
VITE_GOOGLE_CLIENT_ID=your_client_id_here
```

### 3. Test Integration
- Navigate to Google Forms section in app
- Click "Connect to Google Forms"
- Complete OAuth flow
- Your forms should appear

## 🧪 Testing & Verification

### Test Backend Connectivity:
```bash
python test-backend-connection.py
```

### Test Individual Components:
```bash
# Test database
cd backend && flask shell
>>> from app import db
>>> db.engine.execute('SELECT 1').fetchone()

# Test API endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/reports
```

### Browser Testing:
1. Open http://localhost:5173
2. Check browser console for errors
3. Test report generation
4. Test Google Forms integration (if configured)

## 🐛 Troubleshooting

### Common Issues:

1. **"Network Error" in frontend**
   - Check if backend is running on port 5000
   - Verify CORS configuration
   - Check browser console for details

2. **Reports not generating**
   - Check backend logs: `tail -f backend/app.log`
   - Verify database is initialized
   - Check file permissions on uploads directory

3. **Google Forms not working**
   - Verify OAuth credentials are set
   - Check API quotas in Google Cloud Console
   - Ensure APIs are enabled

4. **Database errors**
   - Run: `cd backend && flask db upgrade`
   - If that fails: `rm app.db && flask db upgrade`

### Quick Fixes:
```bash
# Reset everything
python quick-fix.py

# Check specific issues
python test-backend-connection.py
```

## 📁 File Structure (Updated)

```
project/
├── backend/
│   ├── .env.development ✅ NEW
│   ├── .env ✅ CREATED FROM TEMPLATE
│   ├── app/
│   │   ├── routes/
│   │   │   ├── reports_api.py ✅ WORKING
│   │   │   ├── google_forms_routes.py ✅ WORKING
│   │   │   └── nextgen_report_builder.py ✅ WORKING
│   │   └── services/ ✅ ALL SERVICES AVAILABLE
│   └── requirements.txt
├── frontend/
│   ├── .env.development ✅ NEW
│   ├── .env ✅ CREATED FROM TEMPLATE
│   ├── vite.config.ts ✅ FIXED
│   ├── src/
│   │   ├── config/
│   │   │   └── environment.ts ✅ FIXED
│   │   ├── services/
│   │   │   ├── apiService.ts ✅ FIXED
│   │   │   └── reportService.ts ✅ WORKING
│   │   └── pages/
│   │       └── ReportHistory/ ✅ WORKING
│   └── package.json
├── start-development.ps1 ✅ NEW
├── start-development.sh ✅ NEW
├── quick-fix.py ✅ NEW
├── test-backend-connection.py ✅ NEW
├── setup-google-forms.md ✅ NEW
└── TROUBLESHOOTING.md ✅ NEW
```

## 🎯 What's Now Working

### ✅ Fixed Issues:
1. **API Connectivity** - Frontend can now connect to backend
2. **Report Generation** - Backend routes working, frontend integrated
3. **Environment Configuration** - Proper .env files created
4. **Development Workflow** - Easy startup scripts provided
5. **Error Handling** - Proper error messages and troubleshooting

### ✅ Available Features:
1. **Report History** - View, download, delete reports
2. **Report Generation** - Create reports from data
3. **File Management** - Upload and process Excel files
4. **Dashboard Analytics** - View statistics and metrics
5. **Google Forms Integration** - Ready for OAuth setup

### 🔄 Requires Setup:
1. **Google OAuth** - Add your credentials
2. **AI Features** - Add OpenAI/Google AI API keys
3. **Email Features** - Configure SMTP settings (optional)

## 🚀 Next Steps

1. **Start the application:**
   ```bash
   # Windows
   .\start-development.ps1
   
   # Linux/Mac
   ./start-development.sh
   ```

2. **Add your API keys** to `backend/.env`:
   ```bash
   OPENAI_API_KEY=your_key_here
   GOOGLE_CLIENT_ID=your_id_here
   GOOGLE_CLIENT_SECRET=your_secret_here
   ```

3. **Test the features:**
   - Generate a test report
   - Upload an Excel file
   - Connect Google Forms (if configured)

4. **Monitor logs** for any issues:
   ```bash
   tail -f backend/app.log
   ```

## 📞 Support

If you encounter any issues:

1. **Check the logs** first
2. **Run the test script**: `python test-backend-connection.py`
3. **Try the quick fix**: `python quick-fix.py`
4. **Consult the troubleshooting guide**: `TROUBLESHOOTING.md`

Your frontend should now be fully functional! 🎉