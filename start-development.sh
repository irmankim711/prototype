#!/bin/bash
# Development Startup Script for Linux/macOS
# This script starts both backend and frontend in development mode

echo "🚀 Starting AI Report Generator Development Environment"

# Check if Python is installed
if command -v python3 &> /dev/null; then
    echo "✅ Python found: $(python3 --version)"
elif command -v python &> /dev/null; then
    echo "✅ Python found: $(python --version)"
else
    echo "❌ Python not found. Please install Python 3.9+ first."
    exit 1
fi

# Check if Node.js is installed
if command -v node &> /dev/null; then
    echo "✅ Node.js found: $(node --version)"
else
    echo "❌ Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

# Function to start backend
start_backend() {
    echo "🐍 Starting Flask Backend..."
    
    # Navigate to backend directory
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "📦 Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Copy environment file
    if [ ! -f ".env" ]; then
        cp .env.development .env
        echo "📋 Copied .env.development to .env"
    fi
    
    # Initialize database
    echo "🗄️ Initializing database..."
    export FLASK_APP=app
    flask db upgrade 2>/dev/null || {
        echo "⚠️ Database migration failed, trying to initialize..."
        flask db init 2>/dev/null
        flask db migrate -m "Initial migration" 2>/dev/null
        flask db upgrade 2>/dev/null
    }
    
    # Start Flask server in background
    echo "🌐 Starting Flask server on http://localhost:5000..."
    nohup flask run --host=0.0.0.0 --port=5000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    
    # Return to root directory
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "⚛️ Starting React Frontend..."
    
    # Navigate to frontend directory
    cd frontend
    
    # Copy environment file
    if [ ! -f ".env" ]; then
        cp .env.development .env
        echo "📋 Copied .env.development to .env"
    fi
    
    # Install dependencies
    echo "📥 Installing Node.js dependencies..."
    npm install
    
    # Start development server in background
    echo "🌐 Starting Vite dev server on http://localhost:5173..."
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    
    # Return to root directory
    cd ..
}

# Function to check if Redis is running (optional)
test_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            echo "✅ Redis is running"
            return 0
        fi
    fi
    echo "⚠️ Redis not running. Celery tasks will not work."
    echo "   Install Redis: sudo apt-get install redis-server (Ubuntu) or brew install redis (macOS)"
    return 1
}

# Function to stop servers
stop_servers() {
    echo "🛑 Stopping servers..."
    
    if [ -f "backend.pid" ]; then
        kill $(cat backend.pid) 2>/dev/null
        rm backend.pid
        echo "✅ Backend stopped"
    fi
    
    if [ -f "frontend.pid" ]; then
        kill $(cat frontend.pid) 2>/dev/null
        rm frontend.pid
        echo "✅ Frontend stopped"
    fi
    
    exit 0
}

# Set up signal handlers
trap stop_servers SIGINT SIGTERM

# Main execution
echo "🔍 Checking prerequisites..."

# Test Redis (optional)
test_redis

# Start backend
start_backend

# Wait a moment for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Start frontend
start_frontend

echo ""
echo "🎉 Development environment started!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:5000"
echo "📚 API Docs: http://localhost:5000/api/docs (if available)"
echo ""
echo "📋 Logs:"
echo "   Backend: tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop servers: Ctrl+C or run: kill \$(cat backend.pid frontend.pid)"
echo ""
echo "🔧 Next steps:"
echo "   1. Add your OpenAI API key to backend/.env"
echo "   2. Add Google OAuth credentials to both .env files"
echo "   3. Install Redis for background tasks (optional)"

# Wait for user input to stop
echo ""
echo "Press Ctrl+C to stop all servers..."
wait