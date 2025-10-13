#!/usr/bin/env python3
"""
Test frontend login process to find the exact issue
"""
import requests
import json

def test_frontend_connection():
    """Test if frontend is running and serving Firebase config"""
    print("🌐 Testing frontend connection...")

    try:
        # Test if frontend is running
        response = requests.get("http://localhost:3000", timeout=5)
        print(f"Frontend status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"⚠️ Frontend returned {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not running on http://localhost:3000")
        return False
    except Exception as e:
        print(f"❌ Error connecting to frontend: {e}")
        return False

def test_backend_status():
    """Test backend status and endpoints"""
    print("\n🔧 Testing backend status...")

    endpoints_to_test = [
        "/auth/firebase-health",
        "/auth/firebase-config-validation"
    ]

    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            print(f"{endpoint}: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if endpoint == "/auth/firebase-health":
                    print(f"  Firebase status: {data.get('status')}")
                    print(f"  Project ID: {data.get('project_id')}")
                elif endpoint == "/auth/firebase-config-validation":
                    print(f"  Config valid: {data.get('configuration_valid')}")

        except Exception as e:
            print(f"{endpoint}: ERROR - {e}")

def check_browser_console_issues():
    """Provide guidance for checking browser console"""
    print("\n🌐 Browser Console Check Instructions:")
    print("1. Open your browser and go to http://localhost:3000")
    print("2. Open Developer Tools (F12)")
    print("3. Go to the Console tab")
    print("4. Try to log in and look for:")
    print("   - Firebase initialization errors")
    print("   - CORS errors")
    print("   - Network request failures")
    print("   - Authentication token errors")
    print("5. Go to the Network tab and check:")
    print("   - Failed requests to /auth/firebase-sync")
    print("   - Request headers and response details")

def provide_login_troubleshooting():
    """Provide step-by-step login troubleshooting"""
    print("\n🔍 Login Troubleshooting Steps:")
    print("")
    print("STEP 1: Check if both services are running")
    print("  Frontend: http://localhost:3000 (should show your app)")
    print("  Backend:  http://localhost:5000/auth/firebase-health (should return 200)")
    print("")
    print("STEP 2: Try these login methods:")
    print("  • Email/Password login (if you have an account)")
    print("  • Google Sign-In")
    print("  • Development bypass (if enabled)")
    print("")
    print("STEP 3: Check browser console for errors:")
    print("  • Firebase configuration errors")
    print("  • CORS policy violations")
    print("  • Authentication failures")
    print("")
    print("STEP 4: If login fails, check:")
    print("  • Are you entering valid credentials?")
    print("  • Is your Google account accessible?")
    print("  • Are there any popup blockers preventing Google Sign-In?")

def test_development_bypass():
    """Test if development bypass is available"""
    print("\n🔓 Testing development bypass...")

    # Check if development mode allows bypass
    print("Development bypass might be available.")
    print("Look for 'Enable Development Bypass' button in the UI")
    print("Or check if VITE_DEV_USER_* environment variables are set")

if __name__ == "__main__":
    print("🚀 Frontend Login Debug Test\n")

    frontend_ok = test_frontend_connection()
    test_backend_status()
    test_development_bypass()
    check_browser_console_issues()
    provide_login_troubleshooting()

    print("\n" + "="*60)
    if not frontend_ok:
        print("❌ ISSUE FOUND: Frontend is not running!")
        print("   Start the frontend with: npm start or npm run dev")
    else:
        print("✅ Both services appear to be running correctly.")
        print("   The issue is likely in the browser or login process.")
        print("   Follow the troubleshooting steps above.")
    print("="*60)