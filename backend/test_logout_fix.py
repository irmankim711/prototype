"""
Test script to verify logout endpoint functionality
Tests multiple scenarios to ensure logout always succeeds
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_logout_no_token():
    """Test logout without any token"""
    print("\n🧪 Test 1: Logout without token")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        if response.status_code == 200:
            print("   ✅ PASS: Logout succeeded without token")
            return True
        else:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_logout_invalid_token():
    """Test logout with invalid token"""
    print("\n🧪 Test 2: Logout with invalid token")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={
                "Authorization": "Bearer invalid-token-12345",
                "Content-Type": "application/json"
            },
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        if response.status_code == 200:
            print("   ✅ PASS: Logout succeeded with invalid token")
            return True
        else:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_logout_expired_token():
    """Test logout with expired token"""
    print("\n🧪 Test 3: Logout with expired token")
    # This is a JWT token that expired in 2020
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.4Adcj0vbr7-P8Y6TqHvPVRPg-ZhS5t0nVPqLrEjFbvM"

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={
                "Authorization": f"Bearer {expired_token}",
                "Content-Type": "application/json"
            },
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        if response.status_code == 200:
            print("   ✅ PASS: Logout succeeded with expired token")
            return True
        else:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_logout_options():
    """Test OPTIONS request for CORS"""
    print("\n🧪 Test 4: OPTIONS request (CORS preflight)")
    try:
        response = requests.options(
            f"{BASE_URL}/api/auth/logout",
            timeout=5
        )
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ PASS: OPTIONS request succeeded")
            return True
        else:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔍 Testing Logout Endpoint Functionality")
    print("=" * 60)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        print(f"✅ Server is running at {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is not running at {BASE_URL}")
        print("   Please start the backend server first:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        sys.exit(1)

    # Run all tests
    results = []
    results.append(test_logout_no_token())
    results.append(test_logout_invalid_token())
    results.append(test_logout_expired_token())
    results.append(test_logout_options())

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed! Logout endpoint is working correctly.")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} test(s) failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
