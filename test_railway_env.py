"""
Test if Railway has Firebase environment variables set correctly
"""

import requests

RAILWAY_URL = "https://backend-test-6a78.up.railway.app"

def test_firebase_config():
    """Test Firebase configuration on Railway"""

    print("=" * 60)
    print("TESTING RAILWAY FIREBASE CONFIGURATION")
    print("=" * 60)
    print()

    # Test basic health
    print("1️⃣  Testing basic health...")
    try:
        response = requests.get(f"{RAILWAY_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach backend: {e}")
        return

    print()

    # Try to get Firebase debug info (if endpoint exists)
    print("2️⃣  Checking for Firebase debug endpoint...")
    endpoints_to_try = [
        "/api/health/firebase",
        "/api/v1/health/firebase",
        "/health/firebase",
        "/debug/firebase"
    ]

    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{RAILWAY_URL}{endpoint}")
            if response.status_code == 200:
                print(f"✅ Found endpoint: {endpoint}")
                print(f"Response: {response.json()}")
                break
            elif response.status_code == 404:
                continue
            else:
                print(f"⚠️  Endpoint {endpoint} returned: {response.status_code}")
        except:
            continue
    else:
        print("ℹ️  No Firebase debug endpoint found (this is normal)")

    print()

    # Test actual login to see the error
    print("3️⃣  Testing login endpoint (without token)...")
    try:
        response = requests.post(
            f"{RAILWAY_URL}/auth/login",
            json={"email": "test@test.com", "password": "test"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 401:
            error_data = response.json()
            if error_data.get('code') == 'MISSING_AUTH_HEADER':
                print("✅ Backend is working (requires Firebase token as expected)")
            elif error_data.get('code') == 'FIREBASE_NOT_INITIALIZED':
                print("❌ PROBLEM FOUND: Firebase is not initialized on Railway!")
                print("   → Check FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY")
            else:
                print(f"⚠️  Unexpected 401 error: {error_data}")
    except Exception as e:
        print(f"❌ Error testing login: {e}")

    print()
    print("=" * 60)
    print("DIAGNOSIS:")
    print("If you see 'Firebase is not initialized', the problem is:")
    print("1. Missing environment variables in Railway")
    print("2. Incorrect format of FIREBASE_PRIVATE_KEY")
    print("3. Railway hasn't redeployed after adding variables")
    print("=" * 60)

if __name__ == "__main__":
    test_firebase_config()
