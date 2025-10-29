# Railway CLI Deployment Steps

You've just run the Railway link command. Here's what to do next:

## ✅ Step 1: Link Completed (DONE)

You just ran:
```bash
railway link -p f0a3b44a-573d-4e7c-8a99-4b61c5156783
```

This connected your local project to Railway.

---

## 📦 Step 2: Add Database & Redis in Railway Dashboard

Before setting environment variables, add these services:

### In Railway Dashboard (https://railway.app):

1. **Click your project** (should see it now that you're linked)
2. **Add PostgreSQL**:
   - Click "+ New"
   - Select "Database" → "PostgreSQL"
   - Railway will create it and auto-link `DATABASE_URL`

3. **Add Redis**:
   - Click "+ New" again
   - Select "Database" → "Redis"
   - Railway will create it and auto-link `REDIS_URL`

Wait 30 seconds for both to be ready (they'll show green checkmarks).

---

## 🔑 Step 3: Set Environment Variables

Now use Railway CLI to set your environment variables:

### Generate Secret Keys First:
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy both outputs - you'll use them below.

### Set Variables via CLI:

```bash
cd backend

# Required: Application Settings
railway variables --set FLASK_ENV=production
railway variables --set DEBUG=false

# Required: Security (use the keys you just generated!)
railway variables --set SECRET_KEY="paste-your-generated-key-here"
railway variables --set JWT_SECRET_KEY="paste-your-other-generated-key-here"

# Required: CORS (we'll update this after getting Vercel URL)
railway variables --set CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

# Firebase Configuration (get from your Firebase Console)
railway variables --set FIREBASE_API_KEY="your-firebase-api-key"
railway variables --set FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
railway variables --set FIREBASE_PROJECT_ID="your-project-id"
railway variables --set FIREBASE_STORAGE_BUCKET="your-project.firebasestorage.app"
railway variables --set FIREBASE_MESSAGING_SENDER_ID="your-sender-id"
railway variables --set FIREBASE_APP_ID="your-app-id"
railway variables --set FIREBASE_MEASUREMENT_ID="your-measurement-id"

# Google OAuth (get from Google Cloud Console)
railway variables --set GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
railway variables --set GOOGLE_CLIENT_SECRET="GOCSPX-your-secret"

# Optional but recommended
railway variables --set LOG_LEVEL="WARNING"
railway variables --set ENABLE_METRICS="true"
```

**Note:** Database and Redis URLs are auto-linked, so you don't need to set them manually!

---

## 🚀 Step 4: Deploy to Railway

```bash
cd backend
railway up
```

This will:
1. Build your application
2. Deploy to Railway
3. Give you a URL

**Wait 2-5 minutes** for deployment to complete.

---

## 📋 Step 5: Get Your Railway URL

After deployment succeeds:

```bash
railway status
```

Or check the Railway Dashboard - you'll see a URL like:
```
https://prototype-production.up.railway.app
```

**Save this URL!** You'll need it for:
- Vercel frontend configuration
- Google OAuth redirect URI
- CORS settings

---

## 🔧 Step 6: Update Variables with Your Railway URL

Now that you have your Railway backend URL, update these:

```bash
# Update CORS to include your actual domains (keep localhost for testing)
railway variables --set CORS_ORIGINS="http://localhost:3000,http://localhost:5173,https://your-app.vercel.app"

# Update Google OAuth redirect URI
railway variables --set GOOGLE_REDIRECT_URI="https://your-backend-url.up.railway.app/api/google-forms/callback"
```

Replace:
- `your-app.vercel.app` with your actual Vercel domain (after deploying frontend)
- `your-backend-url.up.railway.app` with your actual Railway URL

---

## ✅ Step 7: Verify Deployment

```bash
# Check logs
railway logs

# Check service status
railway status
```

Test your backend:
```bash
curl https://your-backend-url.up.railway.app/api/health
```

Should return: `{"status": "healthy"}` or similar

---

## 🎯 Step 8: Deploy Frontend to Vercel

Now that backend is working:

1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Add New" → "Project"
4. Import your repository
5. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Vite (auto-detected)

6. **Add Environment Variables**:
   ```
   VITE_ENVIRONMENT=production
   VITE_API_BASE_URL=https://your-railway-url.up.railway.app/api
   VITE_BACKEND_URL=https://your-railway-url.up.railway.app

   # Add all Firebase variables (same as backend)
   VITE_FIREBASE_API_KEY=your-value
   # ... etc

   # Google OAuth
   VITE_GOOGLE_CLIENT_ID=your-client-id

   # Feature flags
   VITE_ENABLE_DEBUG_MODE=false
   VITE_ENABLE_AUTH_BYPASS=false
   VITE_ENABLE_HTTPS_ONLY=true
   ```

7. Click "Deploy"

8. Get your Vercel URL (e.g., `https://your-app.vercel.app`)

---

## 🔄 Step 9: Update CORS with Vercel URL

After getting your Vercel URL:

```bash
railway variables --set CORS_ORIGINS="https://your-app.vercel.app,https://your-app-git-test5.vercel.app"
```

This will auto-redeploy Railway with updated CORS.

---

## 🔐 Step 10: Update OAuth & Firebase Settings

### Google Cloud Console:
1. Go to https://console.cloud.google.com/apis/credentials
2. Click your OAuth Client ID
3. **Authorized JavaScript origins** - Add:
   - `https://your-app.vercel.app`
4. **Authorized redirect URIs** - Add:
   - `https://your-app.vercel.app/auth/google/callback`
   - `https://your-railway-url.up.railway.app/api/google-forms/callback`
5. Save

### Firebase Console:
1. Go to https://console.firebase.google.com
2. Authentication → Settings → Authorized domains
3. Add:
   - `your-app.vercel.app`
   - `your-railway-url.up.railway.app`

---

## 🧪 Step 11: Test Everything

1. Visit your Vercel URL
2. Try to sign up/login
3. Test Google Sign-In
4. Test Google Forms integration
5. Check browser console for errors

---

## 📊 Useful Railway CLI Commands

```bash
# View logs
railway logs

# Check status
railway status

# List all variables
railway variables

# Open Railway dashboard
railway open

# Redeploy
railway up

# Shell into your deployment
railway shell
```

---

## 🆘 Troubleshooting

### Issue: "Build failed"
```bash
railway logs
```
Check for missing dependencies in requirements.txt

### Issue: "Application failed to start"
```bash
railway logs --follow
```
Look for Python errors, missing env vars

### Issue: "Database connection failed"
Check that PostgreSQL is linked:
```bash
railway variables | grep DATABASE_URL
```

### Issue: "Module not found"
Make sure you're in the `backend` directory when running `railway up`

### Issue: "CORS error in browser"
Update CORS_ORIGINS to include your Vercel domain

---

## 📈 Next Steps After Successful Deployment

1. ✅ Set up monitoring (Sentry)
2. ✅ Configure custom domain (optional)
3. ✅ Set up automated backups
4. ✅ Add health check monitoring
5. ✅ Scale resources as needed

---

## 💰 Cost Estimate

- Railway: $5 starter credit/month (usually enough for small apps)
- If you exceed, it's pay-as-you-go (~$0.02/hour per resource)
- PostgreSQL + Redis + Web Service ≈ $5-15/month

---

## 🔗 Quick Links

- Railway Dashboard: https://railway.app
- Railway Docs: https://docs.railway.app
- Your Project: https://railway.app/project/f0a3b44a-573d-4e7c-8a99-4b61c5156783

---

Good luck! 🚀

If you get stuck, check the logs first: `railway logs`
