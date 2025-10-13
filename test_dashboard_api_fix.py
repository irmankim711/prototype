#!/usr/bin/env python3
"""
Test Dashboard API Connection Fix
Tests the fixed Firebase authentication for dashboard analytics endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_endpoint(endpoint, headers=None, params=None):
    """Test a specific endpoint and return results"""
    try:
        url = f"{API_BASE}{endpoint}"
        print(f"\n🔍 Testing: {url}")

        if params:
            print(f"📝 Parameters: {params}")

        response = requests.get(url, headers=headers or {}, params=params or {})

        print(f"📊 Status: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")

        if response.text:
            try:
                data = response.json()
                print(f"📦 Response: {json.dumps(data, indent=2)}")
            except:
                print(f"📦 Response (raw): {response.text[:500]}...")

        return {
            'status_code': response.status_code,
            'success': 200 <= response.status_code < 300,
            'data': response.json() if response.text and response.headers.get('content-type', '').startswith('application/json') else response.text,
            'url': url
        }

    except Exception as e:
        print(f"❌ Error testing {endpoint}: {str(e)}")
        return {
            'status_code': 0,
            'success': False,
            'error': str(e),
            'url': endpoint
        }

def main():
    """Test dashboard API endpoints"""
    print("🧪 Dashboard API Connection Test")
    print("=" * 50)

    # Test endpoints (without auth first to check if they're reachable)
    endpoints_to_test = [
        "/analytics/dashboard/stats",
        "/analytics/trends",
        "/analytics/top-forms",
        "/analytics/geographic",
        "/analytics/time-of-day",
        "/analytics/performance-comparison",
        "/analytics/real-time"
    ]

    results = []

    print(f"\n📡 Testing API endpoints without authentication...")

    for endpoint in endpoints_to_test:
        result = test_endpoint(endpoint)
        results.append(result)

    # Summary
    print(f"\n📋 TEST SUMMARY")
    print("=" * 50)

    successful = sum(1 for r in results if r['success'])
    auth_required = sum(1 for r in results if r.get('status_code') == 401)
    server_errors = sum(1 for r in results if 500 <= r.get('status_code', 0) < 600)
    connection_errors = sum(1 for r in results if r.get('status_code') == 0)

    print(f"✅ Successful responses: {successful}")
    print(f"🔒 Authentication required (401): {auth_required}")
    print(f"🔥 Server errors (5xx): {server_errors}")
    print(f"🚫 Connection errors: {connection_errors}")
    print(f"📊 Total endpoints tested: {len(results)}")

    if auth_required == len(endpoints_to_test):
        print(f"\n🎯 RESULT: All endpoints properly require authentication!")
        print(f"✅ Firebase authentication is working correctly")
        print(f"💡 To test with auth, you need a valid Firebase token")
    elif server_errors > 0:
        print(f"\n⚠️  RESULT: Some endpoints have server errors")
        print(f"🔧 Check server logs for detailed error information")
    elif connection_errors > 0:
        print(f"\n❌ RESULT: Cannot connect to server")
        print(f"🔧 Make sure the backend server is running on {BASE_URL}")
    else:
        print(f"\n✅ RESULT: API endpoints are accessible")

    # Test server health
    print(f"\n🏥 Testing server health...")
    health_result = test_endpoint("/health" if "/health" in str(results) else "/")

    if health_result['success']:
        print(f"✅ Server is running and responsive")
    else:
        print(f"❌ Server health check failed")

    return results

if __name__ == "__main__":
    results = main()

    # Exit with appropriate code
    if any(r.get('status_code') == 0 for r in results):
        sys.exit(1)  # Connection errors
    else:
        sys.exit(0)  # Server is running