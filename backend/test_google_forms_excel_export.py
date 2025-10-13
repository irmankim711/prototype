"""
Test script for Google Forms Excel Export functionality
Run this to verify the integration works end-to-end
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_google_forms_excel_export():
    """Test Google Forms Excel export functionality"""

    print("=" * 50)
    print("Google Forms Excel Export Test")
    print("=" * 50)

    # Configuration
    BASE_URL = "http://localhost:5000"
    TEST_FORM_ID = "test_form_id_123"  # Replace with actual Google Form ID

    # Test 1: Check Google Forms service status
    print("\n1. Testing Google Forms service status...")
    try:
        response = requests.get(f"{BASE_URL}/api/google-forms/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("✅ Google Forms service is accessible")
        else:
            print("❌ Google Forms service has issues")

    except Exception as e:
        print(f"❌ Error checking service status: {e}")

    # Test 2: Test Excel export endpoint (requires authentication)
    print(f"\n2. Testing Excel export endpoint for form {TEST_FORM_ID}...")

    # Sample export options
    export_options = {
        "include_analytics": True,
        "date_range": {
            "start": "2024-01-01",
            "end": datetime.now().strftime("%Y-%m-%d")
        },
        "excel_options": {
            "include_form_schema": True,
            "include_submission_metadata": True,
            "formatting": "professional",
            "compression": True
        },
        "max_responses": 100
    }

    try:
        # Note: This will require authentication in a real scenario
        response = requests.post(
            f"{BASE_URL}/api/google-forms/forms/{TEST_FORM_ID}/export-excel",
            json=export_options,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("✅ Excel export endpoint is working")
        elif response.status_code == 401:
            print("⚠️ Authentication required (expected)")
        elif response.status_code == 503:
            print("⚠️ Google Forms service not configured (expected)")
        else:
            print("❌ Unexpected response")

    except Exception as e:
        print(f"❌ Error testing export endpoint: {e}")

    # Test 3: Check if the Google Forms Excel service can be imported
    print("\n3. Testing Google Forms Excel service import...")
    try:
        from app.services.google_forms_excel_service import google_forms_excel_service
        print("✅ Google Forms Excel service imported successfully")

        # Test the service methods
        print("Testing service methods...")
        service = google_forms_excel_service

        # Test filename generation
        filename = service.generate_timestamp_filename("test", "Sample Form")
        print(f"Generated filename: {filename}")

        # Test directory creation
        service.ensure_upload_directory()
        upload_dir_exists = os.path.exists(service.upload_folder)
        print(f"Upload directory exists: {upload_dir_exists}")

        if upload_dir_exists:
            print("✅ Service methods working correctly")
        else:
            print("❌ Service setup issues")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Service error: {e}")

    # Test 4: Test the Google Forms service integration
    print("\n4. Testing Google Forms service integration...")
    try:
        from app.services.google_forms_service import google_forms_service

        if google_forms_service is None:
            print("⚠️ Google Forms service is None (OAuth not configured)")
        elif not google_forms_service.is_enabled():
            print("⚠️ Google Forms service is disabled (OAuth credentials missing)")
        else:
            print("✅ Google Forms service is enabled and ready")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Integration error: {e}")

    # Test 5: Verify required dependencies
    print("\n5. Testing required dependencies...")
    dependencies = [
        "openpyxl",
        "pandas",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client"
    ]

    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep} is available")
        except ImportError:
            print(f"❌ {dep} is missing")

    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

    print("\nNext steps to make it fully functional:")
    print("1. Configure Google OAuth credentials in environment variables:")
    print("   - GOOGLE_CLIENT_ID")
    print("   - GOOGLE_CLIENT_SECRET")
    print("   - GOOGLE_PROJECT_ID")
    print("2. Set up proper authentication flow")
    print("3. Test with a real Google Form ID")
    print("4. Verify Excel file generation and download")

if __name__ == "__main__":
    test_google_forms_excel_export()