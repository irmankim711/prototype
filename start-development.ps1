# Development Startup Script for Windows PowerShell
# This script starts both backend and frontend in development mode

Write-Host "🚀 Starting AI Report Generator Development Environment" -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

# Function to start backend
function Start-Backend {
    Write-Host "🐍 Starting Flask Backend..." -ForegroundColor Yellow
    
    # Navigate to backend directory
    Set-Location backend
    
    # Create virtual environment if it doesn't exist
    if (!(Test-Path "venv")) {
        Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Blue
        python -m venv venv
    }
    
    # Activate virtual environment
    Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
    & "venv\Scripts\Activate.ps1"
    
    # Install dependencies
    Write-Host "📥 Installing Python dependencies..." -ForegroundColor Blue
    pip install -r requirements.txt
    
    # Copy environment file
    if (!(Test-Path ".env")) {
        Copy-Item ".env.development" ".env"
        Write-Host "📋 Copied .env.development to .env" -ForegroundColor Blue
    }
    
    # Initialize database
    Write-Host "🗄️ Initializing database..." -ForegroundColor Blue
    $env:FLASK_APP = "app"
    flask db upgrade 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Database migration failed, trying to initialize..." -ForegroundColor Yellow
        flask db init 2>$null
        flask db migrate -m "Initial migration" 2>$null
        flask db upgrade 2>$null
    }
    
    # Start Flask server
    Write-Host "🌐 Starting Flask server on http://localhost:5000..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; & venv\Scripts\Activate.ps1; flask run --host=0.0.0.0 --port=5000"
    
    # Return to root directory
    Set-Location ..
}

# Function to start frontend
function Start-Frontend {
    Write-Host "⚛️ Starting React Frontend..." -ForegroundColor Yellow
    
    # Navigate to frontend directory
    Set-Location frontend
    
    # Copy environment file
    if (!(Test-Path ".env")) {
        Copy-Item ".env.development" ".env"
        Write-Host "📋 Copied .env.development to .env" -ForegroundColor Blue
    }
    
    # Install dependencies
    Write-Host "📥 Installing Node.js dependencies..." -ForegroundColor Blue
    npm install
    
    # Start development server
    Write-Host "🌐 Starting Vite dev server on http://localhost:5173..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
    
    # Return to root directory
    Set-Location ..
}

# Function to check if Redis is running (optional)
function Test-Redis {
    try {
        $redisTest = redis-cli ping 2>$null
        if ($redisTest -eq "PONG") {
            Write-Host "✅ Redis is running" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "⚠️ Redis not running. Celery tasks will not work." -ForegroundColor Yellow
        Write-Host "   Install Redis from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Yellow
        return $false
    }
}

# Main execution
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Blue

# Test Redis (optional)
Test-Redis

# Start backend
Start-Backend

# Wait a moment for backend to start
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Blue
Start-Sleep -Seconds 5

# Start frontend
Start-Frontend

Write-Host ""
Write-Host "🎉 Development environment started!" -ForegroundColor Green
Write-Host "📱 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "🔧 Backend API: http://localhost:5000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:5000/api/docs (if available)" -ForegroundColor Cyan
Write-Host ""
Write-Host "🛑 To stop servers, close the PowerShell windows or press Ctrl+C in each" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔧 Next steps:" -ForegroundColor Blue
Write-Host "   1. Add your OpenAI API key to backend/.env" -ForegroundColor White
Write-Host "   2. Add Google OAuth credentials to both .env files" -ForegroundColor White
Write-Host "   3. Install Redis for background tasks (optional)" -ForegroundColor White

# Keep this window open
Write-Host "Press any key to exit this startup script..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")