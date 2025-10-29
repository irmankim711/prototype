# Railway Deployment - Quick Fix

## The Issue You're Seeing

Railway couldn't find a start command because it's looking for specific files. I've created the necessary configuration files to fix this.

## Files Created

1. **`backend/Procfile`** - Tells Railway how to start your app
2. **`backend/railway.json`** - Railway-specific configuration
3. **`backend/nixpacks.toml`** - Build configuration for Railway

## What to Do Now in Railway

### Step 1: Push the New Files to GitHub

```bash
git add backend/Procfile backend/railway.json backend/nixpacks.toml
git commit -m "fix: Add Railway deployment configuration"
git push origin Test5
```

### Step 2: In Railway Dashboard

1. Railway should automatically detect the new files and redeploy
2. If not, click the **"Redeploy"** button in Railway
3. Wait 2-5 minutes for deployment to complete

### Step 3: Configure Your Service

In Railway, make sure these settings are correct:

1. Click on your service
2. Go to **Settings** tab
3. Set:
   - **Root Directory**: `backend`
   - **Start Command**: (leave empty - Procfile will handle it)
   - **Build Command**: (leave empty - nixpacks.toml will handle it)

### Step 4: Add Environment Variables

Click **Variables** tab and add:

```bash
# Application
FLASK_ENV=production
DEBUG=false

# Security (generate these!)
SECRET_KEY=<use: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_SECRET_KEY=<use: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Database (if you added PostgreSQL in Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (if you added Redis in Railway)
REDIS_URL=${{Redis.REDIS_URL}}

# CORS (add your Vercel URL later)
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
GOOGLE_REDIRECT_URI=https://your-backend-url.up.railway.app/api/google-forms/callback
```

### Step 5: Check Deployment Logs

1. Go to **Deployments** tab
2. Click on the latest deployment
3. Check the logs for any errors
4. Look for: `✓ Deployment successful` or similar

## Common Issues & Fixes

### Issue: "ModuleNotFoundError"
**Fix**: Make sure all dependencies are in `requirements.txt`

### Issue: "Application failed to respond"
**Fix**:
1. Check that `PORT` environment variable is being used
2. Our configuration already handles this with `$PORT`

### Issue: "Database connection failed"
**Fix**:
1. Make sure PostgreSQL service is linked
2. Verify `DATABASE_URL` variable exists

### Issue: "Build failed"
**Fix**:
1. Check deployment logs for specific error
2. Usually it's a missing dependency in requirements.txt

## After Deployment Success

You'll get a URL like: `https://prototype-production.up.railway.app`

**Save this URL** - you'll need it for:
1. Vercel frontend configuration (`VITE_API_BASE_URL`)
2. Google OAuth redirect URI
3. Firebase authorized domains

## Next Steps

Once Railway deployment works:

1. ✅ Copy your Railway backend URL
2. → Go to Vercel and deploy frontend (use the VERCEL_DEPLOYMENT_GUIDE.md)
3. → Add Railway URL to CORS settings
4. → Update Google OAuth redirect URIs
5. → Test everything!

---

## Quick Command Reference

```bash
# Generate a secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Commit and push config files
git add backend/Procfile backend/railway.json backend/nixpacks.toml
git commit -m "fix: Add Railway deployment configuration"
git push origin Test5
```

---

## Need More Help?

See the complete guide: `VERCEL_DEPLOYMENT_GUIDE.md`

Or Railway docs: https://docs.railway.app/
