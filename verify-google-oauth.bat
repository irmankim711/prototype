@echo off
echo 🔧 Google OAuth Setup Verification Script
echo ========================================

echo.
echo 📋 Step 1: Checking Client ID Configuration

set CLIENT_ID_IN_JSON=1008582896300-73rpvjuobgce2htujji13p7l8tuh6eef.apps.googleusercontent.com

echo Client ID in JSON file: %CLIENT_ID_IN_JSON%

findstr "client_id=" backend\.env
findstr "data-client_id=" frontend\index.html

echo.
echo 📋 Step 2: Checking CORS Configuration

findstr "http://localhost:5173" backend\app\__init__.py
if %errorlevel%==0 (
    echo ✅ CORS allows localhost:5173
) else (
    echo ❌ CORS might not be configured for localhost:5173
)

echo.
echo 📋 Step 3: Checking Vite Configuration

findstr "5173" frontend\vite.config.ts
if %errorlevel%==0 (
    echo ✅ Vite configured for port 5173
) else (
    echo ⚠️  Vite might not be configured for port 5173
)

echo.
echo 📋 Step 4: Checking Dependencies

findstr "flask-cors" backend\requirements.txt
if %errorlevel%==0 (
    echo ✅ Flask-CORS is in requirements.txt
) else (
    echo ❌ Flask-CORS might be missing from requirements.txt
)

findstr "axios" frontend\package.json
if %errorlevel%==0 (
    echo ✅ Axios is in package.json
) else (
    echo ❌ Axios might be missing from package.json
)

echo.
echo 🧪 Next Steps for Testing:
echo 1. Make sure Google Cloud Console has these origins:
echo    - http://localhost:5173 (JavaScript origins)
echo    - http://localhost:5000/api/quick-auth/google-signin (Redirect URIs if needed)
echo.
echo 2. Start the backend:
echo    cd backend ^&^& python run.py
echo.
echo 3. Start the frontend:
echo    cd frontend ^&^& npm run dev
echo.
echo 4. Open http://localhost:5173 and test Google Sign-In
echo.
echo 5. Check browser DevTools for any CORS or JavaScript errors

echo.
echo 🎉 Setup verification complete!
pause
