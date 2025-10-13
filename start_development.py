#!/usr/bin/env python3
"""
Comprehensive Development Environment Startup Script
Starts both backend and frontend services with proper error handling
"""

import os
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path
import requests
import json
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class DevEnvironmentManager:
    def __init__(self):
        self.processes = []
        self.running = True
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        
    def log(self, message, color=Colors.WHITE):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {message}{Colors.END}")
        
    def log_success(self, message):
        self.log(f"✅ {message}", Colors.GREEN)
        
    def log_error(self, message):
        self.log(f"❌ {message}", Colors.RED)
        
    def log_warning(self, message):
        self.log(f"⚠️  {message}", Colors.YELLOW)
        
    def log_info(self, message):
        self.log(f"ℹ️  {message}", Colors.CYAN)

    def check_prerequisites(self):
        """Check if required directories and files exist"""
        self.log_info("Checking prerequisites...")
        
        # Check directories
        if not self.backend_dir.exists():
            self.log_error(f"Backend directory not found: {self.backend_dir}")
            return False
            
        if not self.frontend_dir.exists():
            self.log_error(f"Frontend directory not found: {self.frontend_dir}")
            return False
            
        # Check backend startup script
        backend_script = self.backend_dir / "start_server.py"
        if not backend_script.exists():
            self.log_error(f"Backend startup script not found: {backend_script}")
            return False
            
        # Check frontend package.json
        frontend_package = self.frontend_dir / "package.json"
        if not frontend_package.exists():
            self.log_error(f"Frontend package.json not found: {frontend_package}")
            return False
            
        self.log_success("All prerequisites satisfied")
        return True

    def check_ports(self):
        """Check if required ports are available"""
        self.log_info("Checking port availability...")
        
        def is_port_in_use(port):
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=1)
                return True
            except:
                return False
                
        if is_port_in_use(5000):
            self.log_warning("Port 5000 is already in use (backend may already be running)")
            
        if is_port_in_use(3000):
            self.log_warning("Port 3000 is already in use (frontend may already be running)")

    def start_backend(self):
        """Start the Flask backend server"""
        self.log_info("Starting backend server...")
        
        try:
            # Start backend in a subprocess
            backend_cmd = [sys.executable, "start_server.py"]
            backend_process = subprocess.Popen(
                backend_cmd,
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(("backend", backend_process))
            
            # Monitor backend startup
            def monitor_backend():
                for line in iter(backend_process.stdout.readline, ''):
                    if line.strip():
                        self.log(f"[BACKEND] {line.strip()}", Colors.BLUE)
                        
            backend_thread = threading.Thread(target=monitor_backend)
            backend_thread.daemon = True
            backend_thread.start()
            
            # Wait for backend to be ready
            self.wait_for_backend()
            
        except Exception as e:
            self.log_error(f"Failed to start backend: {e}")
            return False
            
        return True

    def wait_for_backend(self):
        """Wait for backend to be ready"""
        self.log_info("Waiting for backend to be ready...")
        
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:5000/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    self.log_success(f"Backend is ready! Status: {health_data.get('status', 'unknown')}")
                    return True
            except:
                pass
                
            time.sleep(1)
            self.log(f"Backend startup... ({attempt + 1}/{max_attempts})", Colors.YELLOW)
            
        self.log_error("Backend failed to start within timeout period")
        return False

    def start_frontend(self):
        """Start the React frontend development server"""
        self.log_info("Starting frontend development server...")
        
        try:
            # Check if node_modules exists
            node_modules = self.frontend_dir / "node_modules"
            if not node_modules.exists():
                self.log_warning("node_modules not found, running npm install...")
                npm_install = subprocess.run(
                    ["npm", "install"],
                    cwd=self.frontend_dir,
                    capture_output=True,
                    text=True
                )
                if npm_install.returncode != 0:
                    self.log_error(f"npm install failed: {npm_install.stderr}")
                    return False
                self.log_success("npm install completed")
            
            # Start frontend
            frontend_cmd = ["npm", "start"]
            frontend_process = subprocess.Popen(
                frontend_cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(("frontend", frontend_process))
            
            # Monitor frontend startup
            def monitor_frontend():
                for line in iter(frontend_process.stdout.readline, ''):
                    if line.strip():
                        self.log(f"[FRONTEND] {line.strip()}", Colors.GREEN)
                        
            frontend_thread = threading.Thread(target=monitor_frontend)
            frontend_thread.daemon = True
            frontend_thread.start()
            
            self.log_success("Frontend server started")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to start frontend: {e}")
            return False

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.log_warning("Received shutdown signal, cleaning up...")
            self.shutdown()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def shutdown(self):
        """Gracefully shutdown all processes"""
        self.running = False
        self.log_info("Shutting down development environment...")
        
        for name, process in self.processes:
            try:
                self.log_info(f"Stopping {name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    self.log_success(f"{name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    self.log_warning(f"{name} did not stop gracefully, forcing...")
                    process.kill()
                    
            except Exception as e:
                self.log_error(f"Error stopping {name}: {e}")

    def print_status(self):
        """Print current status of services"""
        self.log("", Colors.WHITE)
        self.log("=" * 60, Colors.CYAN)
        self.log("🚀 DEVELOPMENT ENVIRONMENT STATUS", Colors.BOLD + Colors.CYAN)
        self.log("=" * 60, Colors.CYAN)
        
        # Backend status
        try:
            response = requests.get("http://localhost:5000/health", timeout=2)
            if response.status_code == 200:
                health_data = response.json()
                self.log_success(f"Backend: Running on http://localhost:5000")
                self.log_info(f"   Status: {health_data.get('status', 'unknown')}")
                self.log_info(f"   Database: {health_data.get('database', 'unknown')}")
                self.log_info(f"   Environment: {health_data.get('environment', 'unknown')}")
            else:
                self.log_error(f"Backend: HTTP {response.status_code}")
        except:
            self.log_error("Backend: Not responding")
            
        # Frontend status  
        try:
            response = requests.get("http://localhost:3000", timeout=2)
            if response.status_code == 200:
                self.log_success("Frontend: Running on http://localhost:3000")
            else:
                self.log_error(f"Frontend: HTTP {response.status_code}")
        except:
            self.log_warning("Frontend: Not yet ready (normal during startup)")
            
        self.log("=" * 60, Colors.CYAN)
        self.log("📝 NEXT STEPS:", Colors.BOLD + Colors.WHITE)
        self.log("   • Backend API: http://localhost:5000", Colors.WHITE)
        self.log("   • Frontend App: http://localhost:3000", Colors.WHITE)
        self.log("   • Press Ctrl+C to stop all services", Colors.WHITE)
        self.log("=" * 60, Colors.CYAN)
        self.log("", Colors.WHITE)

    def run(self):
        """Main run method"""
        self.log("🔧 Starting Development Environment Manager", Colors.BOLD + Colors.CYAN)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Check prerequisites
        if not self.check_prerequisites():
            sys.exit(1)
            
        # Check ports
        self.check_ports()
        
        # Start backend
        if not self.start_backend():
            self.shutdown()
            sys.exit(1)
            
        # Start frontend
        if not self.start_frontend():
            self.shutdown()
            sys.exit(1)
            
        # Print status
        time.sleep(3)  # Give services time to stabilize
        self.print_status()
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

if __name__ == "__main__":
    manager = DevEnvironmentManager()
    manager.run()
