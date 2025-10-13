#!/usr/bin/env python3
"""
System Diagnostic Script
Quickly diagnose backend/frontend connectivity issues
"""

import os
import sys
import subprocess
import requests
import json
from datetime import datetime
import platform

class SystemDiagnostics:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform.system(),
            'checks': {}
        }
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        
    def print_result(self, check_name, status, details=None):
        emoji = "✅" if status else "❌"
        print(f"{emoji} {check_name}: {'PASS' if status else 'FAIL'}")
        if details:
            print(f"   {details}")
        self.results['checks'][check_name] = {'status': status, 'details': details}
        
    def check_python_processes(self):
        """Check if Python backend processes are running"""
        self.print_header("Backend Process Check")
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                      capture_output=True, text=True)
                processes = result.stdout
            else:
                result = subprocess.run(['pgrep', '-f', 'python.*server'], 
                                      capture_output=True, text=True)
                processes = result.stdout
                
            has_python = 'python' in processes.lower()
            self.print_result("Python processes running", has_python, 
                            f"Found processes: {len(processes.split(chr(10)))} lines" if has_python else "No Python processes found")
                            
        except Exception as e:
            self.print_result("Python processes running", False, f"Error: {e}")
            
    def check_port_availability(self):
        """Check if ports 5000 and 3000 are in use"""
        self.print_header("Port Availability Check")
        
        for port, service in [(5000, "Backend"), (3000, "Frontend")]:
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                    port_in_use = f":{port}" in result.stdout
                else:
                    result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
                    port_in_use = result.returncode == 0
                    
                self.print_result(f"Port {port} ({service})", port_in_use,
                                f"Port is {'occupied' if port_in_use else 'available'}")
                                
            except Exception as e:
                self.print_result(f"Port {port} ({service})", False, f"Error: {e}")
                
    def check_backend_health(self):
        """Check backend API health endpoints"""
        self.print_header("Backend Health Check")
        
        health_endpoints = [
            "http://localhost:5000/health",
            "http://localhost:5000/api/production/health", 
            "http://localhost:5000/api/task-monitoring/health"
        ]
        
        for endpoint in health_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                success = response.status_code == 200
                
                if success:
                    try:
                        data = response.json()
                        details = f"Status: {data.get('status', 'unknown')}"
                        if 'database' in data:
                            details += f", DB: {data['database']}"
                    except:
                        details = f"HTTP {response.status_code}"
                else:
                    details = f"HTTP {response.status_code}"
                    
                self.print_result(f"Health endpoint {endpoint}", success, details)
                
            except requests.ConnectionError:
                self.print_result(f"Health endpoint {endpoint}", False, 
                                "Connection refused - backend not running")
            except requests.Timeout:
                self.print_result(f"Health endpoint {endpoint}", False, 
                                "Timeout - backend not responding")
            except Exception as e:
                self.print_result(f"Health endpoint {endpoint}", False, f"Error: {e}")
                
    def check_api_connectivity(self):
        """Test key API endpoints"""
        self.print_header("API Connectivity Check")
        
        test_endpoints = [
            ("GET", "http://localhost:5000/api/analytics/dashboard/stats", "Analytics"),
            ("GET", "http://localhost:5000/api/public-forms", "Public Forms"),
            ("GET", "http://localhost:5000/api/reports", "Reports")
        ]
        
        for method, endpoint, name in test_endpoints:
            try:
                response = requests.request(method, endpoint, timeout=3)
                # Any response (even 401/404) is better than connection refused
                success = response.status_code < 500
                details = f"HTTP {response.status_code}"
                
                if response.status_code == 401:
                    details += " (Authentication required - normal)"
                elif response.status_code == 404:
                    details += " (Endpoint not found)"
                    
                self.print_result(f"{name} endpoint", success, details)
                
            except requests.ConnectionError:
                self.print_result(f"{name} endpoint", False, "Connection refused")
            except Exception as e:
                self.print_result(f"{name} endpoint", False, f"Error: {e}")
                
    def check_frontend_config(self):
        """Check frontend configuration"""
        self.print_header("Frontend Configuration Check")
        
        config_files = [
            "frontend/package.json",
            "frontend/.env",
            "frontend/.env.development",
            "frontend/src/services/api.ts",
            "frontend/src/services/analyticsService.ts"
        ]
        
        for config_file in config_files:
            exists = os.path.exists(config_file)
            self.print_result(f"Config file {config_file}", exists,
                            "Found" if exists else "Missing")
                            
    def check_backend_config(self):
        """Check backend configuration"""
        self.print_header("Backend Configuration Check")
        
        config_files = [
            "backend/start_server.py",
            "backend/requirements.txt",
            "backend/app/__init__.py",
            "backend/.env"
        ]
        
        for config_file in config_files:
            exists = os.path.exists(config_file)
            self.print_result(f"Config file {config_file}", exists,
                            "Found" if exists else "Missing")
                            
    def generate_recommendations(self):
        """Generate recommendations based on diagnostic results"""
        self.print_header("Recommendations")
        
        checks = self.results['checks']
        
        # Backend not running
        if not any(check['status'] for name, check in checks.items() if 'Health endpoint' in name):
            print("🚨 CRITICAL: Backend server is not running")
            print("   → Solution: cd backend && python start_server.py")
            print()
            
        # Port issues
        if not checks.get('Port 5000 (Backend)', {}).get('status'):
            print("⚠️  Backend port 5000 is not occupied")
            print("   → This usually means the backend server is not running")
            print()
            
        # Configuration issues
        missing_configs = [name for name, check in checks.items() 
                          if 'Config file' in name and not check['status']]
        if missing_configs:
            print("⚠️  Missing configuration files:")
            for config in missing_configs:
                print(f"   → {config}")
            print()
            
        # Success case
        if all(check['status'] for name, check in checks.items() if 'Health endpoint' in name):
            print("🎉 Backend is running and healthy!")
            print("   → All services should be accessible")
            print("   → Frontend should connect successfully")
            print()
            
    def save_report(self):
        """Save diagnostic report to file"""
        report_file = f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Detailed report saved to: {report_file}")
        
    def run_full_diagnostics(self):
        """Run all diagnostic checks"""
        print("🔧 System Diagnostics Tool")
        print(f"Platform: {platform.system()}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.check_python_processes()
        self.check_port_availability()
        self.check_backend_health()
        self.check_api_connectivity()
        self.check_frontend_config()
        self.check_backend_config()
        self.generate_recommendations()
        self.save_report()

if __name__ == "__main__":
    diagnostics = SystemDiagnostics()
    diagnostics.run_full_diagnostics()
