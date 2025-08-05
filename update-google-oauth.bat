@echo off
echo ========================================
echo Google OAuth Client Update Script
echo ========================================
echo.

echo IMPORTANT: Before running this script, you need to:
echo 1. Create a new OAuth client in Google Cloud Console
echo 2. Download the client configuration JSON
echo 3. Have the client_id and client_secret ready
echo.

set /p CLIENT_ID="Enter your new CLIENT_ID: "
set /p CLIENT_SECRET="Enter your new CLIENT_SECRET: "

if "%CLIENT_ID%"=="" (
    echo Error: CLIENT_ID cannot be empty
    pause
    exit /b 1
)

if "%CLIENT_SECRET%"=="" (
    echo Error: CLIENT_SECRET cannot be empty
    pause
    exit /b 1
)

echo.
echo Updating backend credentials.json...

(
echo {
echo   "web": {
echo     "client_id": "%CLIENT_ID%",
echo     "project_id": "stratosys",
echo     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
echo     "token_uri": "https://oauth2.googleapis.com/token",
echo     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
echo     "client_secret": "%CLIENT_SECRET%",
echo     "redirect_uris": ["http://localhost:5000/api/google-forms/callback"]
echo   }
echo }
) > backend\credentials.json

echo Backend credentials.json updated!

echo.
echo Updating backend .env file...

powershell -Command "(Get-Content backend\.env) -replace 'client_id=.*', 'client_id=%CLIENT_ID%' | Set-Content backend\.env"
powershell -Command "(Get-Content backend\.env) -replace 'client_secret=.*', 'client_secret=%CLIENT_SECRET%' | Set-Content backend\.env"

echo Backend .env updated!

echo.
echo Updating frontend .env file...

if exist frontend\.env (
    powershell -Command "(Get-Content frontend\.env) -replace 'VITE_GOOGLE_CLIENT_ID=.*', 'VITE_GOOGLE_CLIENT_ID=%CLIENT_ID%' | Set-Content frontend\.env"
) else (
    echo VITE_API_URL=http://localhost:5000/api > frontend\.env
    echo VITE_GOOGLE_CLIENT_ID=%CLIENT_ID% >> frontend\.env
)

echo Frontend .env updated!

echo.
echo Clearing existing tokens...
if exist backend\tokens (
    rmdir /s /q backend\tokens
    mkdir backend\tokens
    echo Tokens cleared!
) else (
    mkdir backend\tokens
    echo Tokens directory created!
)

echo.
echo ========================================
echo Configuration Update Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Restart your backend server: cd backend ^&^& python run.py
echo 2. Restart your frontend server: cd frontend ^&^& npm run dev
echo 3. Clear browser cookies/cache
echo 4. Try Google Forms authentication again
echo.
pause
