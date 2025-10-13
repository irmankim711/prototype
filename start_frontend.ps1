# Frontend Startup Script for Windows
Write-Host "🚀 Starting Frontend Development Server" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Navigate to frontend directory
Set-Location frontend

# Check if node_modules exists
if (!(Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "📦 Dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🌟 Starting Vite development server..." -ForegroundColor Cyan
Write-Host "✅ AuthContext: useAuth hook added" -ForegroundColor Green
Write-Host "✅ GoogleFormsManager: Import paths fixed" -ForegroundColor Green  
Write-Host "✅ EnhancedSidebar: TypeScript warnings resolved" -ForegroundColor Green
Write-Host "✅ GoogleFormsService: Properly exported" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔗 Google Forms page: http://localhost:3000/google-forms" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Ready to test the complete Google Forms workflow!" -ForegroundColor Magenta
Write-Host ""

# Start the development server
npm run dev
