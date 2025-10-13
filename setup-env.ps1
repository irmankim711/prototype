# Secure Environment Setup Script (PowerShell)
# This script helps developers set up their environment variables securely

Write-Host "🔐 Secure Environment Setup for Automated Report Platform" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "package.json") -or -not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "❌ Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Setting up environment files..." -ForegroundColor Yellow

# Backend environment setup
if (-not (Test-Path "backend\.env")) {
    Write-Host "📝 Creating backend\.env from template..." -ForegroundColor Cyan
    Copy-Item "backend\.env.template" "backend\.env"
    Write-Host "✅ Created backend\.env" -ForegroundColor Green
    Write-Host "⚠️  Please edit backend\.env and add your actual API keys and secrets" -ForegroundColor Yellow
} else {
    Write-Host "ℹ️  backend\.env already exists" -ForegroundColor Blue
}

# Frontend environment setup
if (-not (Test-Path "frontend\.env")) {
    Write-Host "📝 Creating frontend\.env from template..." -ForegroundColor Cyan
    Copy-Item "frontend\.env.template" "frontend\.env"
    Write-Host "✅ Created frontend\.env" -ForegroundColor Green
    Write-Host "⚠️  Please edit frontend\.env and add your actual API keys" -ForegroundColor Yellow
} else {
    Write-Host "ℹ️  frontend\.env already exists" -ForegroundColor Blue
}

# Check if .env files are in .gitignore
Write-Host "🔍 Checking .gitignore configuration..." -ForegroundColor Yellow
if (Select-String -Path ".gitignore" -Pattern "\.env" -Quiet) {
    Write-Host "✅ .env files are properly ignored by Git" -ForegroundColor Green
} else {
    Write-Host "❌ WARNING: .env files are not in .gitignore!" -ForegroundColor Red
    Write-Host "Adding .env to .gitignore..." -ForegroundColor Yellow
    Add-Content -Path ".gitignore" -Value ".env"
    Write-Host "✅ Added .env to .gitignore" -ForegroundColor Green
}

# Check pre-commit hook
if (Test-Path ".git\hooks\pre-commit") {
    Write-Host "✅ Pre-commit hook is installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Pre-commit hook is not installed" -ForegroundColor Yellow
    Write-Host "This hook prevents accidental commits of API keys" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Magenta
Write-Host "1. Edit backend\.env with your actual API keys and secrets"
Write-Host "2. Edit frontend\.env with your actual API keys"
Write-Host "3. Never commit these .env files to version control"
Write-Host "4. Use .env.template files as reference for required variables"
Write-Host ""
Write-Host "🔒 Security Tips:" -ForegroundColor Magenta
Write-Host "- Use different API keys for development and production"
Write-Host "- Rotate your API keys regularly"
Write-Host "- Use environment-specific configurations"
Write-Host "- Monitor your API key usage in the respective dashboards"
Write-Host ""
Write-Host "✅ Environment setup complete!" -ForegroundColor Green
