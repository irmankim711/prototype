# Step-by-Step Vercel Deployment Guide

This guide will walk you through deploying your Automated Report Platform to Vercel (frontend) and Railway/Render (backend).

## Overview

- **Frontend**: Vercel (React + Vite)
- **Backend**: Railway or Render (Flask + Python)
- **Database**: Supabase or Railway PostgreSQL
- **Redis**: Upstash
- **Firebase**: Already configured

---

## Part 1: Deploy Backend First (Required)

You need a backend URL before deploying the frontend. Choose one option:

### Option A: Railway (Recommended - Easiest)

#### Step 1: Sign up for Railway
1. Go to https://railway.app
2. Click "Login" and sign in with GitHub
3. Authorize Railway to access your repositories

#### Step 2: Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Select your repository: `irmankim711/prototype`
4. Railway will detect it's a Python app

#### Step 3: Configure Backend
1. In Railway dashboard, click on your service
2. Go to "Settings" tab
3. Set **Root Directory**: `backend`
4. Set **Start Command**: `gunicorn wsgi:app`

#### Step 4: Add PostgreSQL Database
1. Click "+ New" in your project
2. Select "Database" → "PostgreSQL"
3. Railway will create and link the database automatically
4. Copy the `DATABASE_URL` from the database service

#### Step 5: Add Redis
1. Click "+ New" again
2. Select "Database" → "Redis"
3. Copy the `REDIS_URL` from the Redis service

#### Step 6: Add Environment Variables
1. Go back to your backend service
2. Click "Variables" tab
3. Click "+ Add Variables"
4. Add the following (one by one or bulk):

```bash
FLASK_ENV=production
DEBUG=false
SECRET_KEY=<generate-with-python-secrets>
JWT_SECRET_KEY=<generate-with-python-secrets>

# Database (automatically set by Railway if linked)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# CORS - Add your Vercel URL later
CORS_ORIGINS=https://your-app.vercel.app

# Firebase
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret

# Optional
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=WARNING
```

**To generate SECRET_KEY and JWT_SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Run this twice to get two different keys.

#### Step 7: Deploy
1. Railway will automatically deploy
2. Wait for deployment to complete (2-5 minutes)
3. Copy your backend URL (e.g., `https://your-app.up.railway.app`)
4. **Save this URL - you'll need it for Vercel!**

---

### Option B: Render (Alternative)

#### Step 1: Sign up for Render
1. Go to https://render.com
2. Sign in with GitHub

#### Step 2: Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select `irmankim711/prototype`

#### Step 3: Configure Service
- **Name**: automated-report-backend
- **Region**: Choose closest to you
- **Branch**: `Test5` or `main`
- **Root Directory**: `backend`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app`
- **Instance Type**: Free (to start)

#### Step 4: Add Environment Variables
Add the same environment variables as Railway above.

#### Step 5: Create PostgreSQL Database
1. Go to Dashboard → "New +" → "PostgreSQL"
2. Name it and create
3. Copy the "Internal Database URL"
4. Add to your web service as `DATABASE_URL`

#### Step 6: Add Redis
Use Upstash for Redis:
1. Go to https://upstash.com
2. Create free Redis database
3. Copy Redis URL
4. Add as `REDIS_URL` to Render

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Install Vercel CLI (Optional)
```bash
npm install -g vercel
```

### Step 2: Sign up for Vercel
1. Go to https://vercel.com
2. Click "Sign Up"
3. Sign up with GitHub
4. Authorize Vercel

### Step 3: Import Project
1. Go to Vercel Dashboard
2. Click "Add New..." → "Project"
3. Import your GitHub repository: `irmankim711/prototype`
4. Click "Import"

### Step 4: Configure Project
Vercel will detect it's a Vite project automatically:

- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

Click "Continue"

### Step 5: Add Environment Variables

Click "Environment Variables" and add:

```
VITE_ENVIRONMENT=production
VITE_API_BASE_URL=<YOUR_RAILWAY_BACKEND_URL>/api
VITE_BACKEND_URL=<YOUR_RAILWAY_BACKEND_URL>

# Firebase (same values as backend)
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
VITE_FIREBASE_MEASUREMENT_ID=your-measurement-id

# Google OAuth (public client ID)
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# Feature flags
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_PWA=false
VITE_ENABLE_DEBUG_MODE=false
VITE_ENABLE_AUTH_BYPASS=false
VITE_ENABLE_DEV_TOOLS=false

# Security
VITE_ENABLE_HTTPS_ONLY=true
VITE_ENABLE_CONTENT_SECURITY_POLICY=true
```

**Important:** Replace `<YOUR_RAILWAY_BACKEND_URL>` with your actual Railway URL (e.g., `https://your-app.up.railway.app`)

### Step 6: Deploy
1. Click "Deploy"
2. Wait for deployment (2-5 minutes)
3. Vercel will give you a URL like: `https://your-app.vercel.app`

---

## Part 3: Update CORS and OAuth Settings

### Update Backend CORS

#### Railway:
1. Go to your Railway backend service
2. Click "Variables"
3. Update `CORS_ORIGINS` to include your Vercel URL:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,https://your-app-git-test5.vercel.app
   ```
4. Click "Deploy" or it will auto-redeploy

#### Render:
1. Go to your Render web service
2. Click "Environment"
3. Update `CORS_ORIGINS`
4. Save changes (auto-redeploys)

### Update Google OAuth Redirect URIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services → Credentials
3. Click on your OAuth 2.0 Client ID
4. Under "Authorized JavaScript origins" add:
   - `https://your-app.vercel.app`
5. Under "Authorized redirect URIs" add:
   - `https://your-app.vercel.app/auth/google/callback`
   - `https://YOUR_BACKEND_URL/api/google-forms/callback`
6. Click "Save"

### Update Firebase Authorized Domains

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Authentication → Settings → Authorized domains
4. Click "Add domain"
5. Add: `your-app.vercel.app`
6. Add: `your-backend.up.railway.app` (or Render URL)
7. Click "Save"

---

## Part 4: Verify Deployment

### Test Frontend
1. Visit your Vercel URL: `https://your-app.vercel.app`
2. The app should load
3. Check browser console for errors

### Test Backend Connection
1. Open browser DevTools → Network tab
2. Try to login
3. Check if API calls are going to your backend URL
4. Verify responses are coming back

### Test Firebase Authentication
1. Try to sign up/login with email
2. Try Google Sign-In
3. Check Firebase Console → Authentication → Users to see if users are created

### Test Google Forms Integration
1. Login to the app
2. Try to connect Google Forms
3. Authorize the OAuth flow
4. Verify you can see your forms

---

## Part 5: Common Issues and Fixes

### Issue: CORS Error
**Error:** "Access to fetch at '...' from origin '...' has been blocked by CORS policy"

**Fix:**
1. Check backend `CORS_ORIGINS` includes your Vercel URL
2. Make sure there are no trailing slashes
3. Restart backend service after updating

### Issue: Firebase Auth Not Working
**Error:** "Firebase: Error (auth/unauthorized-domain)"

**Fix:**
1. Add your Vercel domain to Firebase Authorized domains
2. Wait 5 minutes for DNS to propagate

### Issue: Google OAuth Redirect Mismatch
**Error:** "redirect_uri_mismatch"

**Fix:**
1. Copy the exact redirect URI from the error message
2. Add it to Google Cloud Console OAuth settings
3. Make sure it matches exactly (https vs http, trailing slash, etc.)

### Issue: Environment Variables Not Working
**Error:** Variables show as `undefined`

**Fix:**
1. In Vercel, all environment variables must start with `VITE_`
2. Redeploy after adding env vars: Settings → Deployments → Redeploy

### Issue: Build Fails
**Error:** Build errors in Vercel

**Fix:**
1. Test build locally: `cd frontend && npm run build`
2. Fix any TypeScript errors
3. Make sure all dependencies are in `package.json`
4. Push fixes to GitHub
5. Vercel will auto-redeploy

---

## Part 6: Set Up Custom Domain (Optional)

### In Vercel:
1. Go to your project → Settings → Domains
2. Click "Add"
3. Enter your domain (e.g., `myapp.com`)
4. Follow DNS configuration instructions
5. Wait for DNS propagation (can take up to 48 hours)

### Update All URLs:
1. Update `CORS_ORIGINS` in backend to include custom domain
2. Update Google OAuth redirect URIs
3. Update Firebase authorized domains

---

## Part 7: Monitoring and Maintenance

### Enable Vercel Analytics
1. Go to Vercel project → Analytics
2. Enable Web Analytics
3. View metrics on dashboard

### Enable Sentry Error Tracking
1. Sign up at https://sentry.io
2. Create new project
3. Copy DSN
4. Add to both frontend and backend env vars:
   ```
   VITE_SENTRY_DSN=your-dsn
   SENTRY_DSN=your-dsn
   ```

### Set Up Uptime Monitoring
Use services like:
- UptimeRobot (https://uptimerobot.com) - Free
- Better Uptime (https://betteruptime.com) - Free tier
- Pingdom - Monitor both frontend and backend

---

## Quick Reference: URLs You'll Need

| Service | URL | Where to Get It |
|---------|-----|-----------------|
| Frontend | `https://your-app.vercel.app` | Vercel dashboard after deploy |
| Backend | `https://your-app.up.railway.app` | Railway dashboard |
| Database | `postgresql://user:pass@host/db` | Railway/Render database page |
| Redis | `redis://host:port` | Upstash or Railway Redis |
| Firebase Console | https://console.firebase.google.com | - |
| Google Cloud Console | https://console.cloud.google.com | - |

---

## Deployment Checklist

Before going live:

- [ ] Backend deployed and accessible
- [ ] Database created and connected
- [ ] Redis created and connected
- [ ] All environment variables set correctly
- [ ] Frontend deployed to Vercel
- [ ] CORS configured with Vercel URL
- [ ] Google OAuth redirect URIs updated
- [ ] Firebase authorized domains updated
- [ ] Test authentication (email/password)
- [ ] Test Google Sign-In
- [ ] Test Google Forms integration
- [ ] No console errors in browser
- [ ] API calls working correctly
- [ ] Sentry set up for error tracking
- [ ] Monitoring set up
- [ ] Custom domain configured (if applicable)

---

## Next Steps After Deployment

1. **Test Everything Thoroughly**
   - Create test accounts
   - Try all features
   - Test on mobile devices
   - Test in different browsers

2. **Set Up Backups**
   - Railway/Render have automatic backups
   - Set up additional backup strategy if needed

3. **Monitor Performance**
   - Check Vercel Analytics
   - Monitor backend logs in Railway/Render
   - Set up alerts for errors

4. **Scale as Needed**
   - Upgrade Railway/Render plan if needed
   - Add more backend instances
   - Enable Vercel Pro for better performance

---

## Support and Resources

- **Vercel Docs**: https://vercel.com/docs
- **Railway Docs**: https://docs.railway.app
- **Render Docs**: https://render.com/docs
- **Firebase Docs**: https://firebase.google.com/docs
- **Vite Docs**: https://vitejs.dev

---

## Estimated Costs

| Service | Free Tier | Paid Plan |
|---------|-----------|-----------|
| Vercel | ✅ Unlimited (hobby) | $20/month (Pro) |
| Railway | $5 credit/month | Pay as you go (~$5-20/month) |
| Render | ✅ 750 hours/month | $7/month (Starter) |
| Supabase | ✅ 500MB database | $25/month (Pro) |
| Upstash | ✅ 10,000 commands/day | $0.20/100k commands |
| Firebase | ✅ Generous free tier | Pay as you go |

**Total estimated cost to start**: **$0-5/month** (using free tiers)

---

Good luck with your deployment! 🚀

If you encounter any issues, check the troubleshooting section or refer to the service documentation.
