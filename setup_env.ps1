# PowerShell script to set up environment files
Write-Host "Setting up environment files with new credentials..." -ForegroundColor Green

# Backend .env file
$backendEnv = @"
# Database Configuration
DATABASE_URL=sqlite:///instance/app.db

# Flask Configuration
FLASK_APP=backend.app
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this-in-production

# OpenAI Configuration - REPLACE WITH YOUR NEW API KEY
OPENAI_API_KEY=sk-your-new-openai-api-key-here

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Email Configuration (if using SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Redis Configuration (if using)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS Configuration
CORS_ORIGIN=http://localhost:3000
"@

# Auth Backend .env file
$authEnv = @"
# Server Configuration
PORT=4000
NODE_ENV=development

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/auth_database

# JWT Configuration
JWT_ACCESS_SECRET=your-jwt-access-secret-change-this
JWT_REFRESH_SECRET=your-jwt-refresh-secret-change-this

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
EMAIL_FROM=your-email@gmail.com

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS Configuration
CORS_ORIGIN=http://localhost:3000

# Google OAuth (if using)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
"@

# Write the files
$backendEnv | Out-File -FilePath "backend/.env" -Encoding UTF8
$authEnv | Out-File -FilePath "auth-backend/.env" -Encoding UTF8

Write-Host "Environment files created!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Replace the placeholder values with your actual credentials:" -ForegroundColor Yellow
Write-Host "1. Replace 'sk-your-new-openai-api-key-here' with your new OpenAI API key" -ForegroundColor Red
Write-Host "2. Update database URLs, email settings, and other credentials" -ForegroundColor Red
Write-Host "3. Change all 'your-*-change-this' values to secure random strings" -ForegroundColor Red
Write-Host ""
Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "- backend/.env" -ForegroundColor White
Write-Host "- auth-backend/.env" -ForegroundColor White 