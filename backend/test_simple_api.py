#!/usr/bin/env python3
"""
Test simple API functionality
"""
import requests
import time
import subprocess
import sys
import os

def start_flask_app():
    """Start Flask app in background"""
    try:
        # Start Flask app
        process = subprocess.Popen([
            sys.executable, 'run.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for app to start
        print("🚀 Starting Flask app...")
        time.sleep(5)  # Give app time to start
        
        return process
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        return None

def test_api_endpoints():
    """Test basic API endpoints"""
    base_url = "http://127.0.0.1:5000"
    
    print(f"🔍 Testing API endpoints at {base_url}")
    
    # Test health check or root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ Root endpoint: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test API status
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        print(f"✅ API status endpoint: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API status endpoint failed: {e}")
    
    # Test user registration endpoint
    try:
        test_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=test_data,
            timeout=10
        )
        print(f"✅ User registration endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ User registration endpoint failed: {e}")

def main():
    """Main test function"""
    print("=" * 50)
    print("TESTING FLASK API FUNCTIONALITY")
    print("=" * 50)
    
    # Start Flask app
    process = start_flask_app()
    if not process:
        print("❌ Could not start Flask app")
        return
    
    try:
        # Test API endpoints
        test_api_endpoints()
        
    finally:
        # Clean up - stop Flask app
        print("\n🛑 Stopping Flask app...")
        process.terminate()
        process.wait()
        print("✅ Flask app stopped")

if __name__ == "__main__":
    main()
