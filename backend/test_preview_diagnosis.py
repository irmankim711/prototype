"""
Test script to diagnose preview endpoint issues
"""
import requests
import json

# Test configuration
BASE_URL = "http://localhost:5000"  # Adjust if needed
REPORT_ID = 26  # Use the report ID from your recent commit message

def test_preview_endpoints():
    """Test all preview endpoints to see which ones work"""

    print("="*60)
    print("TESTING PREVIEW ENDPOINTS")
    print("="*60)

    endpoints = [
        f"{BASE_URL}/api/v1/nextgen/reports/{REPORT_ID}/preview",
        f"{BASE_URL}/api/reports/{REPORT_ID}/preview",
        f"{BASE_URL}/api/excel-to-pdf/preview/{REPORT_ID}",
    ]

    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing: {endpoint}")
        print(f"{'='*60}")

        try:
            response = requests.get(endpoint, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\nResponse JSON:")
                    print(json.dumps(data, indent=2))

                    # Check if response has expected fields
                    if 'success' in data:
                        print(f"\n✓ Has 'success' field: {data['success']}")
                    if 'preview' in data:
                        print(f"✓ Has 'preview' field")
                        preview = data['preview']
                        if isinstance(preview, dict):
                            print(f"  - Preview keys: {list(preview.keys())}")
                    if 'preview_url' in data:
                        print(f"✓ Has 'preview_url': {data['preview_url']}")
                    if 'preview_type' in data:
                        print(f"✓ Has 'preview_type': {data['preview_type']}")

                except json.JSONDecodeError as e:
                    print(f"\n✗ Failed to parse JSON: {e}")
                    print(f"Raw content (first 500 chars):")
                    print(response.text[:500])
            else:
                print(f"\n✗ Request failed")
                try:
                    error_data = response.json()
                    print(f"Error response:")
                    print(json.dumps(error_data, indent=2))
                except:
                    print(f"Raw error (first 500 chars):")
                    print(response.text[:500])

        except requests.exceptions.RequestException as e:
            print(f"\n✗ Request error: {e}")

    # Test download endpoints
    print(f"\n{'='*60}")
    print("TESTING DOWNLOAD ENDPOINTS")
    print(f"{'='*60}")

    download_endpoints = [
        f"{BASE_URL}/api/v1/nextgen/reports/{REPORT_ID}/download/pdf",
        f"{BASE_URL}/api/v1/nextgen/reports/{REPORT_ID}/download/docx",
    ]

    for endpoint in download_endpoints:
        print(f"\nTesting: {endpoint}")
        try:
            response = requests.head(endpoint, timeout=10)
            print(f"Status Code: {response.status_code}")
            if 'content-type' in response.headers:
                print(f"Content-Type: {response.headers['content-type']}")
            if 'content-length' in response.headers:
                size_kb = int(response.headers['content-length']) / 1024
                print(f"File Size: {size_kb:.2f} KB")
        except requests.exceptions.RequestException as e:
            print(f"✗ Request error: {e}")

if __name__ == "__main__":
    test_preview_endpoints()
