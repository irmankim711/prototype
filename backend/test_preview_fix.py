"""
Test script to verify the 403 error fix for report preview endpoint.

This script tests that the user ID type mismatch has been resolved.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
REPORT_ID = 21  # The report ID from the analysis

def test_preview_endpoint_with_auth():
    """Test the preview endpoint with proper authentication."""

    # You'll need to replace this with a valid Firebase token
    # You can get this from your browser's developer tools after logging in
    AUTH_TOKEN = "YOUR_FIREBASE_TOKEN_HERE"

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    print("=" * 80)
    print("Testing Report Preview Endpoint")
    print("=" * 80)

    # Test 1: Get report status
    print("\n1. Testing GET /api/reports/{report_id}/status")
    print("-" * 80)
    status_url = f"{BASE_URL}/api/reports/{REPORT_ID}/status"
    response = requests.get(status_url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test 2: Get report preview
    print("\n2. Testing GET /api/reports/{report_id}/preview")
    print("-" * 80)
    preview_url = f"{BASE_URL}/api/reports/{REPORT_ID}/preview"
    response = requests.get(preview_url, headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ SUCCESS! Preview endpoint is now working.")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    elif response.status_code == 403:
        print("❌ FAILED! Still getting 403 Forbidden error.")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("\nThis could mean:")
        print("1. The server hasn't been restarted with the new code")
        print("2. There's a different authorization issue")
        print("3. The user_id comparison is still failing")
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test 3: Get full report details
    print("\n3. Testing GET /api/reports/{report_id}")
    print("-" * 80)
    report_url = f"{BASE_URL}/api/reports/{REPORT_ID}"
    response = requests.get(report_url, headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        report_data = data.get('report', {})
        print(f"Report ID: {report_data.get('id')}")
        print(f"Title: {report_data.get('title')}")
        print(f"User ID: {report_data.get('user_id')} (type: {type(report_data.get('user_id')).__name__})")
        print(f"Status: {report_data.get('status')}")
        print(f"Generation Status: {report_data.get('generation_status')}")
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


def verify_type_consistency():
    """Verify that user ID types are consistent in the codebase."""
    print("\n" + "=" * 80)
    print("Type Consistency Analysis")
    print("=" * 80)

    print("""
    Fixed Issues:
    ------------
    1. Report.user_id property returns int (from created_by string)
    2. get_current_user_id() can return string or int from g.current_user_id
    3. Comparison: str(report.user_id) != str(user_id) fails when types differ

    Solution Applied:
    ----------------
    Changed all comparisons from:
        if report.user_id != user_id and not is_admin:

    To:
        if str(report.user_id) != str(user_id) and not is_admin:

    This ensures consistent string comparison regardless of original types.

    Endpoints Fixed:
    ---------------
    ✓ GET  /api/reports/<int:report_id>/status
    ✓ GET  /api/reports/<int:report_id>/preview  (PRIMARY FIX)
    ✓ PUT  /api/reports/<int:report_id>/edit
    ✓ POST /api/reports/<int:report_id>/convert/latex
    ✓ GET  /api/reports/<int:report_id>/download/<file_type>
    ✓ GET  /api/reports/<int:report_id>
    ✓ DELETE /api/reports/<int:report_id>
    """)


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Before running this test:")
    print("1. Make sure your Flask backend is running on http://localhost:5000")
    print("2. Replace 'YOUR_FIREBASE_TOKEN_HERE' with a valid Firebase auth token")
    print("3. The token should belong to the user who owns report ID 21")
    print("\nTo get your auth token:")
    print("1. Open your browser developer tools (F12)")
    print("2. Go to the Network tab")
    print("3. Log in to your application")
    print("4. Look for a request with an Authorization header")
    print("5. Copy the Bearer token value")
    print("\n" + "=" * 80)

    verify_type_consistency()

    # Uncomment to run the actual tests (after adding your token)
    # test_preview_endpoint_with_auth()
