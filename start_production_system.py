#!/usr/bin/env python3
"""
Production System Startup Script
Comprehensive startup script for the automated report generation system
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_section(title):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print("-" * 40)

def check_redis():
    """Check if Redis is running"""
    print_section("Checking Redis Connection")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Redis is not accessible: {e}")
        print("💡 To start Redis:")
        print("   - Windows: Install Redis via WSL or Docker")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
        print("   - Or use: redis-server")
        return False

def check_database():
    """Check database connectivity"""
    print_section("Checking Database Connection")
    try:
        # Change to backend directory
        os.chdir('backend')
        sys.path.insert(0, os.getcwd())
        
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            db.engine.execute('SELECT 1')
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and configured")
        return False
    finally:
        os.chdir('..')

def check_celery():
    """Check Celery configuration"""
    print_section("Checking Celery Configuration")
    try:
        os.chdir('backend')
        sys.path.insert(0, os.getcwd())
        
        from app.celery_enhanced import celery
        print("✅ Celery configuration is valid")
        print(f"   📡 Broker: {celery.conf.broker_url}")
        print(f"   💾 Backend: {celery.conf.result_backend}")
        print(f"   📋 Queues: {[q.name for q in celery.conf.task_queues]}")
        return True
    except Exception as e:
        print(f"❌ Celery configuration failed: {e}")
        return False
    finally:
        os.chdir('..')

def check_frontend():
    """Check if frontend dependencies are installed"""
    print_section("Checking Frontend Dependencies")
    try:
        if os.path.exists('frontend/package.json'):
            print("✅ Frontend package.json found")
            if os.path.exists('frontend/node_modules'):
                print("✅ Frontend node_modules found")
                return True
            else:
                print("⚠️  Frontend node_modules not found")
                print("💡 Run: cd frontend && npm install")
                return False
        else:
            print("❌ Frontend package.json not found")
            return False
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        return False

def start_redis_docker():
    """Start Redis using Docker"""
    print_section("Starting Redis with Docker")
    try:
        result = subprocess.run([
            'docker', 'run', '-d', 
            '--name', 'redis-production',
            '-p', '6379:6379',
            'redis:alpine'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Redis started successfully with Docker")
            print("   Container ID:", result.stdout.strip())
            return True
        else:
            print(f"❌ Failed to start Redis: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker or start Redis manually")
        return False

def start_backend():
    """Start the Flask backend"""
    print_section("Starting Flask Backend")
    try:
        os.chdir('backend')
        print("💡 To start the backend, run in a new terminal:")
        print("   cd backend")
        print("   python -m flask run --host=0.0.0.0 --port=5000")
        print("   Or: python start_development.py")
        return True
    except Exception as e:
        print(f"❌ Backend startup failed: {e}")
        return False
    finally:
        os.chdir('..')

def start_celery_worker():
    """Start Celery worker"""
    print_section("Starting Celery Worker")
    try:
        os.chdir('backend')
        print("💡 To start Celery worker, run in a new terminal:")
        print("   cd backend")
        print("   python start_celery_worker.py")
        print("   Or: celery -A app.celery_enhanced.celery worker --loglevel=info")
        return True
    except Exception as e:
        print(f"❌ Celery worker startup failed: {e}")
        return False
    finally:
        os.chdir('..')

def start_frontend():
    """Start the React frontend"""
    print_section("Starting React Frontend")
    try:
        if os.path.exists('frontend'):
            print("💡 To start the frontend, run in a new terminal:")
            print("   cd frontend")
            print("   npm start")
            print("   Or: npm run dev")
            return True
        else:
            print("❌ Frontend directory not found")
            return False
    except Exception as e:
        print(f"❌ Frontend startup failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print_section("Testing API Endpoints")
    try:
        # Wait a bit for backend to start
        time.sleep(2)
        
        # Test health endpoint
        try:
            response = requests.get('http://localhost:5000/api/health/', timeout=5)
            if response.status_code == 200:
                print("✅ Health endpoint is working")
                return True
            else:
                print(f"⚠️  Health endpoint returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health endpoint not accessible: {e}")
            print("💡 Make sure the backend is running on port 5000")
            return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main startup function"""
    print_header("Production-Ready Automated Report System")
    print("This script will check all components and provide startup instructions")
    
    # Check all components
    redis_ok = check_redis()
    db_ok = check_database()
    celery_ok = check_celery()
    frontend_ok = check_frontend()
    
    print_header("System Status Summary")
    print(f"Redis: {'✅' if redis_ok else '❌'}")
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"Celery: {'✅' if celery_ok else '❌'}")
    print(f"Frontend: {'✅' if frontend_ok else '❌'}")
    
    # Start Redis if needed
    if not redis_ok:
        print_header("Starting Redis")
        if start_redis_docker():
            print("⏳ Waiting for Redis to be ready...")
            time.sleep(3)
            if check_redis():
                print("✅ Redis is now ready!")
            else:
                print("❌ Redis still not accessible")
        else:
            print("❌ Could not start Redis automatically")
    
    # Provide startup instructions
    print_header("Startup Instructions")
    print("Follow these steps to start the complete system:")
    
    print("\n1️⃣  Start Redis (if not already running):")
    print("   docker run -d --name redis-production -p 6379:6379 redis:alpine")
    
    print("\n2️⃣  Start Flask Backend (Terminal 1):")
    print("   cd backend")
    print("   python -m flask run --host=0.0.0.0 --port=5000")
    
    print("\n3️⃣  Start Celery Worker (Terminal 2):")
    print("   cd backend")
    print("   python start_celery_worker.py")
    
    print("\n4️⃣  Start React Frontend (Terminal 3):")
    print("   cd frontend")
    print("   npm start")
    
    print("\n5️⃣  Test the System:")
    print("   Backend: http://localhost:5000")
    print("   Frontend: http://localhost:3000")
    print("   Health Check: http://localhost:5000/api/health/")
    
    print_header("Quick Start Commands")
    print("Copy and paste these commands in separate terminals:")
    
    print("\n🔧 Terminal 1 (Backend):")
    print("cd backend && python -m flask run --host=0.0.0.0 --port=5000")
    
    print("\n🔄 Terminal 2 (Celery):")
    print("cd backend && python start_celery_worker.py")
    
    print("\n⚛️  Terminal 3 (Frontend):")
    print("cd frontend && npm start")
    
    print_header("System Ready!")
    print("🎉 Your production-ready automated report system is configured!")
    print("📚 Check PRODUCTION_READY_SYSTEM_README.md for detailed documentation")
    print("🧪 Use API_TESTING_EXAMPLES.md for testing the endpoints")

if __name__ == '__main__':
    main()
