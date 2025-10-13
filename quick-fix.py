#!/usr/bin/env python3
"""
Quick Fix Script for Common Issues
This script automatically fixes the most common development issues
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def run_command(cmd, cwd=None, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_and_fix_environment():
    """Check and fix environment configuration"""
    print("🔧 Checking environment configuration...")
    
    # Check backend .env
    backend_env = Path("backend/.env")
    if not backend_env.exists():
        print("   📋 Creating backend/.env from template...")
        shutil.copy("backend/.env.development", "backend/.env")
    
    # Check frontend .env
    frontend_env = Path("frontend/.env")
    if not frontend_env.exists():
        print("   📋 Creating frontend/.env from template...")
        shutil.copy("frontend/.env.development", "frontend/.env")
    
    print("   ✅ Environment files ready")

def check_and_fix_dependencies():
    """Check and install missing dependencies"""
    print("🔧 Checking dependencies...")
    
    # Check Python dependencies
    if Path("backend/requirements.txt").exists():
        print("   📦 Checking Python dependencies...")
        os.chdir("backend")
        
        # Create venv if it doesn't exist
        if not Path("venv").exists():
            print("   🐍 Creating Python virtual environment...")
            success, _, _ = run_command("python -m venv venv")
            if not success:
                success, _, _ = run_command("python3 -m venv venv")
            
            if not success:
                print("   ❌ Failed to create virtual environment")
                return False
        
        # Install dependencies
        if os.name == 'nt':  # Windows
            activate_cmd = "venv\\Scripts\\activate && pip install -r requirements.txt"
        else:  # Linux/Mac
            activate_cmd = "source venv/bin/activate && pip install -r requirements.txt"
        
        success, _, _ = run_command(activate_cmd)
        if success:
            print("   ✅ Python dependencies installed")
        else:
            print("   ⚠️ Some Python dependencies may have failed to install")
        
        os.chdir("..")
    
    # Check Node.js dependencies
    if Path("frontend/package.json").exists():
        print("   📦 Checking Node.js dependencies...")
        os.chdir("frontend")
        
        if not Path("node_modules").exists():
            print("   📥 Installing Node.js dependencies...")
            success, _, _ = run_command("npm install")
            if success:
                print("   ✅ Node.js dependencies installed")
            else:
                print("   ❌ Failed to install Node.js dependencies")
                os.chdir("..")
                return False
        
        os.chdir("..")
    
    return True

def check_and_fix_database():
    """Check and fix database issues"""
    print("🔧 Checking database...")
    
    os.chdir("backend")
    
    # Set environment variable
    os.environ["FLASK_APP"] = "app"
    
    # Check if database exists
    if not Path("app.db").exists() and not Path("instance/app.db").exists():
        print("   🗄️ Database not found, initializing...")
        
        # Try to upgrade first (in case migrations exist)
        success, _, _ = run_command("flask db upgrade")
        
        if not success:
            print("   🔄 Initializing database from scratch...")
            # Initialize migrations
            success, _, _ = run_command("flask db init")
            if success:
                # Create initial migration
                success, _, _ = run_command('flask db migrate -m "Initial migration"')
                if success:
                    # Apply migration
                    success, _, _ = run_command("flask db upgrade")
        
        if success:
            print("   ✅ Database initialized")
        else:
            print("   ⚠️ Database initialization may have issues")
    else:
        print("   ✅ Database exists")
    
    os.chdir("..")

def check_ports():
    """Check if required ports are available"""
    print("🔧 Checking ports...")
    
    import socket
    
    def is_port_open(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    
    # Check backend port (5000)
    if is_port_open(5000):
        print("   ⚠️ Port 5000 is already in use (backend)")
    else:
        print("   ✅ Port 5000 is available (backend)")
    
    # Check frontend port (5173)
    if is_port_open(5173):
        print("   ⚠️ Port 5173 is already in use (frontend)")
    else:
        print("   ✅ Port 5173 is available (frontend)")

def check_api_connectivity():
    """Test API connectivity"""
    print("🔧 Testing API connectivity...")
    
    try:
        import requests
        
        # Test if backend is running
        try:
            response = requests.get("http://localhost:5000/api/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ Backend API is responding")
                return True
            else:
                print(f"   ⚠️ Backend API returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ❌ Backend API is not running")
        except requests.exceptions.Timeout:
            print("   ❌ Backend API timeout")
        except Exception as e:
            print(f"   ❌ Backend API error: {e}")
        
    except ImportError:
        print("   ⚠️ requests library not available for testing")
    
    return False

def create_test_data():
    """Create some test data for development"""
    print("🔧 Creating test data...")
    
    # This would create sample forms, reports, etc.
    # For now, just create necessary directories
    
    directories = [
        "backend/uploads",
        "backend/uploads/excel",
        "backend/uploads/templates",
        "backend/static",
        "backend/static/reports",
        "backend/instance",
        "backend/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("   ✅ Required directories created")

def main():
    """Main fix routine"""
    print("🚀 Quick Fix Script for AI Report Generator")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run fixes
    try:
        check_and_fix_environment()
        
        if not check_and_fix_dependencies():
            print("❌ Dependency installation failed")
            sys.exit(1)
        
        check_and_fix_database()
        create_test_data()
        check_ports()
        
        # Test connectivity if backend is running
        api_working = check_api_connectivity()
        
        print("\n" + "=" * 50)
        print("🎉 Quick fix completed!")
        
        if api_working:
            print("✅ Backend is running and responding")
            print("🌐 Frontend: http://localhost:5173")
            print("🔧 Backend: http://localhost:5000")
        else:
            print("⚠️ Backend is not running. Start it with:")
            if os.name == 'nt':
                print("   .\\start-development.ps1")
            else:
                print("   ./start-development.sh")
        
        print("\n🔧 Next steps:")
        print("1. Add your API keys to backend/.env")
        print("2. Configure Google OAuth credentials")
        print("3. Test the application")
        
    except KeyboardInterrupt:
        print("\n❌ Fix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()