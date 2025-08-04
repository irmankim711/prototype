#!/usr/bin/env python3
"""
Quick setup and test script for the automated report generation system
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return e

def check_backend_dependencies():
    """Check if backend dependencies are installed"""
    print("Checking backend dependencies...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    requirements_file = backend_dir / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    # Check if virtual environment exists
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("Creating virtual environment...")
        run_command("python -m venv venv", cwd=backend_dir)
    
    # Install dependencies
    print("Installing backend dependencies...")
    if os.name == 'nt':  # Windows
        pip_path = venv_dir / "Scripts" / "pip"
    else:  # Unix/Linux/Mac
        pip_path = venv_dir / "bin" / "pip"
    
    run_command(f"{pip_path} install -r requirements.txt", cwd=backend_dir)
    return True

def check_frontend_dependencies():
    """Check if frontend dependencies are installed"""
    print("Checking frontend dependencies...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json not found")
        return False
    
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("Installing frontend dependencies...")
        run_command("npm install", cwd=frontend_dir)
    
    return True

def start_backend():
    """Start the Flask backend"""
    print("Starting backend server...")
    
    backend_dir = Path("backend")
    
    # Start the backend in the background
    if os.name == 'nt':  # Windows
        python_path = backend_dir / "venv" / "Scripts" / "python"
    else:  # Unix/Linux/Mac
        python_path = backend_dir / "venv" / "bin" / "python"
    
    # Start backend server
    backend_process = subprocess.Popen(
        [str(python_path), "app.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("Backend starting... waiting 10 seconds")
    time.sleep(10)
    
    return backend_process

def start_frontend():
    """Start the React frontend"""
    print("Starting frontend development server...")
    
    frontend_dir = Path("frontend")
    
    # Start frontend in the background
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("Frontend starting... waiting 10 seconds")
    time.sleep(10)
    
    return frontend_process

def test_system():
    """Run the system test"""
    print("Running system test...")
    
    result = run_command("python test_automation_system.py", check=False)
    
    if result.returncode == 0:
        print("✅ System test completed successfully!")
        return True
    else:
        print("❌ System test failed")
        return False

def main():
    """Main setup and test function"""
    print("🚀 Automated Report Generation System - Quick Setup & Test")
    print("=" * 70)
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the project root directory")
        print("   (the directory containing 'backend' and 'frontend' folders)")
        sys.exit(1)
    
    try:
        # Setup backend
        if not check_backend_dependencies():
            print("❌ Backend setup failed")
            return
        
        # Setup frontend
        if not check_frontend_dependencies():
            print("❌ Frontend setup failed")
            return
        
        # Start services
        print("\n🔄 Starting services...")
        backend_process = start_backend()
        
        # Test the backend
        print("\n🧪 Testing the system...")
        test_success = test_system()
        
        if test_success:
            print("\n✅ Backend is working! Now starting frontend...")
            frontend_process = start_frontend()
            
            print("\n🌐 System is ready!")
            print("- Backend: http://localhost:5000")
            print("- Frontend: http://localhost:3000")
            print("- API Documentation: http://localhost:5000/api/docs")
            print("\nPress Ctrl+C to stop all services")
            
            try:
                # Keep services running
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping services...")
                backend_process.terminate()
                frontend_process.terminate()
                print("✅ Services stopped")
        else:
            print("\n❌ Backend test failed. Stopping backend...")
            backend_process.terminate()
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
