# Production Environment Setup Guide

This guide will help you configure all environment variables needed for production deployment of the Automated Report Platform.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Backend Environment Variables](#backend-environment-variables)
3. [Frontend Environment Variables](#frontend-environment-variables)
4. [Firebase Setup](#firebase-setup)
5. [Google OAuth Setup](#google-oauth-setup)
6. [Database Setup](#database-setup)
7. [Redis Setup](#redis-setup)
8. [Optional Services](#optional-services)
9. [Security Checklist](#security-checklist)
10. [Deployment Checklist](#deployment-checklist)

---

## Quick Start

### 1. Backend Environment Setup

```bash
cd backend
cp .env.production.template .env.production
# Edit .env.production with your actual values
nano .env.production
```

### 2. Frontend Environment Setup

```bash
cd frontend
cp .env.production.template .env.production
# Edit .env.production with your actual values
nano .env.production
```

---

## Backend Environment Variables

### Critical Settings (Required)

#### Application Security
```bash
# Generate secure random keys:
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

Add these to `backend/.env.production`:
- `SECRET_KEY` - Flask secret key for session encryption
- `JWT_SECRET_KEY` - JWT token signing key
- `ENCRYPTION_KEY` - Additional encryption key for sensitive data

#### Database Configuration
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

**Where to get:**
- Use your PostgreSQL hosting service (Heroku, Railway, Supabase, AWS RDS, etc.)
- Format: `postgresql://username:password@host.domain.com:5432/dbname`

**Example providers:**
- Supabase: Free tier available - https://supabase.com
- Railway: https://railway.app
- Heroku Postgres: https://www.heroku.com/postgres
- AWS RDS: https://aws.amazon.com/rds/

#### CORS Origins
```bash
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

**Critical:** Set this to your actual frontend production URLs!

### Firebase Configuration (Required)

```bash
FIREBASE_API_KEY=AIzaSyCGpr8w2sPsngexBYBg6ktNE64IWENtD2Q
FIREBASE_AUTH_DOMAIN=report-automation-57f6e.firebaseapp.com
FIREBASE_PROJECT_ID=report-automation-57f6e
FIREBASE_STORAGE_BUCKET=report-automation-57f6e.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=87279819935
FIREBASE_APP_ID=1:87279819935:web:9f78b1c4c2efe16ad4d6aa
```

**Where to get:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: `report-automation-57f6e`
3. Go to Project Settings > General
4. Scroll to "Your apps" section
5. Copy the config values

**Service Account (for backend):**
1. Go to Firebase Console > Project Settings > Service Accounts
2. Click "Generate new private key"
3. Download the JSON file
4. Set: `FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json`

### Google OAuth Configuration (Required for Google Forms)

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/google-forms/callback
```

**Where to get:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Create OAuth 2.0 Client ID (or use existing)
4. Add authorized redirect URIs:
   - `https://your-production-domain.com/api/google-forms/callback`
   - `https://your-production-domain.com/auth/google/callback`
5. Copy Client ID and Client Secret

**Required APIs to enable:**
- Google Forms API
- Google Sheets API
- Google Drive API

### Redis Configuration (Required)

```bash
REDIS_URL=redis://host:port/0
RATELIMIT_STORAGE_URL=redis://host:port/1
CELERY_BROKER_URL=redis://host:port/0
```

**Where to get:**
- Upstash: Free tier - https://upstash.com/
- Redis Cloud: https://redis.com/try-free/
- Railway: https://railway.app
- Heroku Redis: https://www.heroku.com/redis

---

## Frontend Environment Variables

### Critical Settings (Required)

#### API Configuration
```bash
VITE_API_BASE_URL=https://api.your-domain.com/api
VITE_BACKEND_URL=https://api.your-domain.com
```

**Set these to your actual backend production URLs!**

#### Firebase Configuration
```bash
# Same values as backend
VITE_FIREBASE_API_KEY=AIzaSyCGpr8w2sPsngexBYBg6ktNE64IWENtD2Q
VITE_FIREBASE_AUTH_DOMAIN=report-automation-57f6e.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=report-automation-57f6e
VITE_FIREBASE_STORAGE_BUCKET=report-automation-57f6e.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=87279819935
VITE_FIREBASE_APP_ID=1:87279819935:web:9f78b1c4c2efe16ad4d6aa
VITE_FIREBASE_MEASUREMENT_ID=G-R2HGN102D3
```

#### Firebase App Check (Recommended for Security)
```bash
VITE_RECAPTCHA_SITE_KEY=your-recaptcha-v3-site-key
VITE_APP_CHECK_ENABLED=true
```

**Where to get reCAPTCHA key:**
1. Go to [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Register your site with reCAPTCHA v3
3. Add your domain
4. Copy the site key (public, safe for frontend)

**Enable Firebase App Check:**
1. Go to Firebase Console > App Check
2. Register your web app
3. Select reCAPTCHA v3 as provider
4. Add your reCAPTCHA site key

#### Google OAuth Client ID
```bash
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

Use the same Client ID from Google Cloud Console (it's public, safe for frontend).

### Production Feature Flags
```bash
VITE_ENVIRONMENT=production
VITE_ENABLE_DEBUG_MODE=false
VITE_ENABLE_AUTH_BYPASS=false
VITE_ENABLE_DEV_TOOLS=false
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_PWA=true
```

---

## Firebase Setup

### 1. Authentication Setup
1. Go to Firebase Console > Authentication
2. Enable sign-in methods:
   - ✅ Email/Password
   - ✅ Google
3. Add authorized domains:
   - `your-production-domain.com`
   - `www.your-production-domain.com`

### 2. Firestore Database Setup
1. Go to Firebase Console > Firestore Database
2. Create database in production mode
3. Set up security rules (see `backend/firebase.json`)
4. Deploy rules: `firebase deploy --only firestore:rules`

### 3. Storage Setup
1. Go to Firebase Console > Storage
2. Set up security rules for file uploads
3. Create buckets as needed

### 4. App Check Setup (Recommended)
1. Go to Firebase Console > App Check
2. Register your web app
3. Configure reCAPTCHA v3
4. Enable enforcement after testing

---

## Google OAuth Setup

### 1. Create OAuth Consent Screen
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. APIs & Services > OAuth consent screen
3. Choose "External" user type
4. Fill in app information:
   - App name: "Automated Report Platform"
   - Support email: your-email@domain.com
   - Authorized domains: your-production-domain.com
5. Add scopes:
   - Google Forms API
   - Google Sheets API
   - Google Drive API

### 2. Create OAuth 2.0 Client
1. APIs & Services > Credentials
2. Create OAuth 2.0 Client ID
3. Application type: Web application
4. Authorized JavaScript origins:
   - `https://your-production-domain.com`
5. Authorized redirect URIs:
   - `https://your-production-domain.com/auth/google/callback`
   - `https://your-production-domain.com/api/google-forms/callback`

### 3. Enable Required APIs
1. APIs & Services > Library
2. Enable:
   - ✅ Google Forms API
   - ✅ Google Sheets API
   - ✅ Google Drive API
   - ✅ Google Calendar API (if using)

---

## Database Setup

### PostgreSQL Production Setup

**Recommended Providers:**
1. **Supabase** (Free tier, easy setup)
   - Go to https://supabase.com
   - Create project
   - Copy connection string from Settings > Database

2. **Railway** (Free tier, one-click deploy)
   - Go to https://railway.app
   - Create PostgreSQL database
   - Copy DATABASE_URL from variables

3. **Heroku Postgres**
   - Add Heroku Postgres addon
   - Copy DATABASE_URL from config vars

### Initial Database Setup
```bash
# Run migrations
cd backend
python migrate_to_production.py

# Or use Alembic
alembic upgrade head
```

---

## Redis Setup

### Recommended Providers

1. **Upstash** (Free tier, serverless)
   - Go to https://upstash.com
   - Create Redis database
   - Copy connection URL
   - Supports: Redis commands, REST API

2. **Redis Cloud** (Free 30MB)
   - Go to https://redis.com/try-free/
   - Create database
   - Copy connection string

3. **Railway**
   - One-click Redis deployment
   - Copy REDIS_URL from variables

### Configuration
```bash
# Main Redis (sessions, cache)
REDIS_URL=redis://default:password@host:port/0

# Rate limiting (separate DB)
RATELIMIT_STORAGE_URL=redis://default:password@host:port/1

# Celery (background tasks)
CELERY_BROKER_URL=redis://default:password@host:port/0
```

---

## Optional Services

### Email Service (SMTP)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

**Gmail Setup:**
1. Enable 2FA on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the generated password (not your regular password)

### Sentry (Error Monitoring)
```bash
SENTRY_DSN=https://key@sentry.io/project-id
```

**Setup:**
1. Go to https://sentry.io
2. Create project
3. Copy DSN from project settings

### OpenAI API (AI Features)
```bash
OPENAI_API_KEY=sk-your-api-key
```

**Setup:**
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Set billing limits to avoid surprises

### Google Gemini API
```bash
GEMINI_API_KEY=your-gemini-api-key
```

**Setup:**
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Enable Gemini API

---

## Security Checklist

### Before Going Live

- [ ] Generate strong SECRET_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY
- [ ] Set DEBUG=false in production
- [ ] Configure proper CORS_ORIGINS (no wildcards!)
- [ ] Enable FORCE_HTTPS=true
- [ ] Set SESSION_COOKIE_SECURE=true
- [ ] Enable Firebase App Check
- [ ] Set up rate limiting properly
- [ ] Review Firestore security rules
- [ ] Enable Sentry for error tracking
- [ ] Set up proper logging (LOG_LEVEL=WARNING)
- [ ] Remove any development/test accounts
- [ ] Disable VITE_ENABLE_AUTH_BYPASS
- [ ] Disable VITE_ENABLE_DEBUG_MODE
- [ ] Enable VITE_ENABLE_HTTPS_ONLY
- [ ] Set up SSL certificates (HTTPS)
- [ ] Configure security headers
- [ ] Set up database backups
- [ ] Enable Redis persistence
- [ ] Review and test OAuth redirect URIs
- [ ] Set up monitoring and alerts

---

## Deployment Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] Database migrations completed
- [ ] Redis connection tested
- [ ] Firebase configured and tested
- [ ] Google OAuth configured and tested
- [ ] SSL certificates installed
- [ ] Domain DNS configured
- [ ] Firewall rules configured
- [ ] Backup strategy in place

### Testing

- [ ] Run backend tests: `pytest`
- [ ] Run frontend tests: `npm test`
- [ ] Test authentication flow
- [ ] Test Google Forms integration
- [ ] Test report generation
- [ ] Test file uploads
- [ ] Test email notifications (if configured)
- [ ] Load testing completed
- [ ] Security scan completed

### Post-Deployment

- [ ] Monitor error logs
- [ ] Check Sentry for errors
- [ ] Monitor database performance
- [ ] Monitor Redis memory usage
- [ ] Check API response times
- [ ] Verify CORS working correctly
- [ ] Test all critical user flows
- [ ] Set up uptime monitoring
- [ ] Configure backup schedule
- [ ] Document deployment process

---

## Common Deployment Platforms

### Vercel (Frontend)
```bash
cd frontend
npm run build
vercel --prod
```

Environment variables: Add in Vercel dashboard under Settings > Environment Variables

### Railway (Backend + Database + Redis)
```bash
cd backend
railway up
```

Environment variables: Add in Railway dashboard under Variables

### Heroku (Full Stack)
```bash
# Backend
cd backend
heroku create your-app-backend
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
git push heroku main

# Frontend
cd frontend
heroku create your-app-frontend
heroku buildpacks:set heroku/nodejs
git push heroku main
```

### Docker Deployment
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

---

## Environment Variables Reference

### Backend (.env.production)
See `backend/.env.production.template` for complete list with descriptions.

### Frontend (.env.production)
See `frontend/.env.production.template` for complete list with descriptions.

---

## Need Help?

### Documentation
- Firebase: https://firebase.google.com/docs
- Google OAuth: https://developers.google.com/identity/protocols/oauth2
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/documentation

### Support
- Check existing documentation in `/docs` folder
- Review Firebase setup guides in repository
- Check authentication troubleshooting guide

---

## Security Notes

1. **Never commit `.env.production` files to Git**
2. **Use environment variable management services** (Railway variables, Heroku config vars, Vercel env vars)
3. **Rotate secrets regularly** (every 90 days recommended)
4. **Use different keys for each environment** (dev, staging, prod)
5. **Enable 2FA** on all service accounts
6. **Monitor for security vulnerabilities** (Dependabot, Snyk)
7. **Keep dependencies updated**
8. **Review access logs regularly**
9. **Set up alerts** for unusual activity
10. **Have an incident response plan**

---

Good luck with your deployment! 🚀
