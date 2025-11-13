# Deployment Guide - Form Automation Platform

## Quick Start Deployment

### Prerequisites Checklist
- [x] Python 3.8+ installed
- [x] Node.js 16+ installed
- [x] Git repository up to date (Test5 branch)
- [ ] Anthropic API key ready
- [ ] Database configured (PostgreSQL/SQLite)
- [ ] Firebase credentials (if using Firebase auth)

## Step 1: Install Backend Dependencies

```bash
cd backend

# Install all dependencies including the new anthropic package
pip install -r requirements.txt

# Verify anthropic is installed
pip show anthropic
```

**Expected Output:**
```
Name: anthropic
Version: 0.39.0 or higher
```

## Step 2: Configure Environment Variables

### A. Development Environment

Edit `backend/.env` and add your Anthropic API key:

```env
# Add this line to your existing .env file
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
```

### B. Production Environment

If deploying to production, edit `backend/.env.production`:

```env
# Anthropic Claude Configuration (PRODUCTION READY)
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here

# Make sure these are also set:
FLASK_ENV=production
DEBUG=false
```

### C. Get Your Anthropic API Key

1. Visit: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy the key and paste it in your `.env` file

## Step 3: Start the Backend Server

### Option A: Development Mode (Recommended for local testing)

```bash
cd backend
python run.py
```

**You should see:**
```
🚀 Starting Flask application...
📁 Loading environment variables...
🎯 Environment: development
🐛 Debug Mode: True
📦 Creating Flask application...
✅ Flask application created successfully
🌐 Starting server on 127.0.0.1:5000
==========================================
🚀 Server is starting...
==========================================
```

### Option B: Production Mode

```bash
cd backend
python run_production.py
```

Or using Gunicorn (better for production):

```bash
cd backend
gunicorn --config gunicorn.conf.py app:create_app
```

## Step 4: Verify Backend is Running

Open a new terminal and test:

```bash
# Test basic health endpoint
curl http://localhost:5000/

# Test template endpoint (should show 3 templates now)
curl http://localhost:5000/api/nextgen-report-builder/templates

# Test AI status endpoint
curl http://localhost:5000/api/nextgen-report-builder/ai/status
```

**Expected AI Status Response:**
```json
{
  "success": true,
  "ai_enabled": true,
  "service": "Claude AI (Anthropic)",
  "model": "claude-sonnet-4",
  "features": {
    "report_generation": true,
    "executive_summary": true,
    "data_insights": true,
    "visualization_suggestions": true
  }
}
```

## Step 5: Start the Frontend Application

### Install Frontend Dependencies (First time only)

```bash
cd frontend
npm install
```

### Start Development Server

```bash
cd frontend
npm run dev
```

**You should see:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

## Step 6: Access Your Application

1. **Open Browser:** http://localhost:5173/
2. **Login** with your credentials
3. **Test Template Loading:**
   - Navigate to Report Builder
   - Click "Generate Automated Report"
   - Check if "Select Report Template" dropdown shows all 3 templates:
     - Laporan FU Puncak Alam (Final)
     - Report Template (Copy)
     - Laporan FU Puncak Alam

## Step 7: Test Claude AI Features

### Test AI Report Generation

1. Upload an Excel file
2. Select a template
3. Click "Generate Report"
4. The AI should now enhance the report with intelligent insights

### Test via API (Optional)

```bash
# Test AI executive summary (requires authentication token)
curl -X POST http://localhost:5000/api/nextgen-report-builder/ai/executive-summary \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "data": [
      {"month": "Jan", "revenue": 50000},
      {"month": "Feb", "revenue": 55000}
    ]
  }'
```

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"

**Solution:**
```bash
# Check if .env file exists
ls -la backend/.env

# Verify the key is in the file
grep ANTHROPIC backend/.env

# Make sure there are no extra spaces:
# ✅ CORRECT: ANTHROPIC_API_KEY=sk-ant-xxxxx
# ❌ WRONG:   ANTHROPIC_API_KEY = sk-ant-xxxxx (spaces around =)
```

### Issue: "ModuleNotFoundError: No module named 'anthropic'"

**Solution:**
```bash
cd backend
pip install anthropic>=0.39.0
```

### Issue: Templates Not Showing

**Solution:**
```bash
# Pull latest changes
git pull origin Test5

# Restart backend server
# Press Ctrl+C to stop
python run.py
```

### Issue: CORS Errors

**Solution:**
Backend should already be configured for CORS. If you see CORS errors, verify:

```bash
# Check if frontend URL is in allowed origins
grep CORS_ORIGINS backend/.env
```

Should include: `http://localhost:5173`

### Issue: Database Connection Error

**Solution:**
```bash
# For development with SQLite (default)
cd backend
python -c "from app import create_app; app = create_app(); print('✅ Database OK')"

# If using PostgreSQL, verify DATABASE_URL in .env
```

## Production Deployment Options

### Option 1: Traditional Server (VPS/Cloud)

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-pip nginx postgresql redis-server

# Setup backend
cd backend
pip install -r requirements.txt
gunicorn --config gunicorn.conf.py app:create_app

# Build frontend
cd frontend
npm run build:prod

# Serve frontend with nginx
sudo cp -r dist/* /var/www/html/
```

### Option 2: Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

Deploy:
```bash
docker-compose up -d
```

### Option 3: Vercel + Railway/Render

**Frontend (Vercel):**
```bash
cd frontend
vercel --prod
```

**Backend (Railway/Render):**
1. Connect your GitHub repository
2. Select `Test5` branch
3. Set environment variables in dashboard
4. Deploy automatically

## Environment Variables Summary

### Required for Basic Operation
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

### Required for Claude AI Features
```env
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Optional (Firebase Auth)
```env
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
```

## Post-Deployment Checklist

- [ ] Backend server is running on port 5000
- [ ] Frontend is accessible on port 5173 (dev) or 80/443 (prod)
- [ ] Template dropdown shows all 3 templates
- [ ] AI status endpoint returns `"ai_enabled": true`
- [ ] Can upload Excel files successfully
- [ ] Can generate reports with templates
- [ ] Claude AI enhancements are working
- [ ] User authentication is functioning
- [ ] Database is properly connected
- [ ] All API endpoints return expected responses

## Monitoring & Logs

### View Backend Logs
```bash
# Development
tail -f backend/logs/app.log

# Production (with systemd)
journalctl -u backend-app -f
```

### View Frontend Logs
```bash
# Development
# Logs appear in terminal where npm run dev is running

# Production (nginx)
tail -f /var/log/nginx/access.log
```

## Performance Optimization

### Backend
```bash
# Use Gunicorn with multiple workers
gunicorn --workers 4 --threads 2 --bind 0.0.0.0:5000 app:create_app
```

### Frontend
```bash
# Build optimized production bundle
npm run build:prod

# Analyze bundle size
npm run analyze:bundle
```

## Security Checklist

- [ ] Change default SECRET_KEY and JWT_SECRET_KEY
- [ ] Use HTTPS in production (configure nginx with SSL)
- [ ] Keep API keys in environment variables (never commit to git)
- [ ] Enable rate limiting on API endpoints
- [ ] Configure CORS properly (only allow specific origins)
- [ ] Use strong passwords for database
- [ ] Regularly update dependencies
- [ ] Monitor for security vulnerabilities (Dependabot alerts)

## Backup & Recovery

### Database Backup
```bash
# PostgreSQL
pg_dump your_database > backup_$(date +%Y%m%d).sql

# SQLite
cp backend/database.db backup_$(date +%Y%m%d).db
```

### Configuration Backup
```bash
# Backup environment files (without API keys)
cp backend/.env backend/.env.backup
```

## Support & Resources

- **Claude AI Docs:** https://docs.anthropic.com/
- **Flask Docs:** https://flask.palletsprojects.com/
- **React + Vite:** https://vitejs.dev/
- **Project Issues:** https://github.com/irmankim711/prototype/issues

## Quick Commands Reference

```bash
# Backend
cd backend
python run.py                    # Start development server
python run_production.py         # Start production server
pip install -r requirements.txt  # Install dependencies
python test_claude_ai_integration.py  # Test AI features

# Frontend
cd frontend
npm run dev                      # Start development server
npm run build:prod              # Build for production
npm install                     # Install dependencies

# Git
git pull origin Test5           # Get latest changes
git status                      # Check current state
git log --oneline -5           # View recent commits

# System
ps aux | grep python           # Check if backend is running
ps aux | grep node            # Check if frontend is running
lsof -i :5000                 # Check what's using port 5000
lsof -i :5173                 # Check what's using port 5173
```

---

**Last Updated:** 2025-11-03
**Branch:** Test5
**Version:** 1.0.0 with Claude AI Integration
