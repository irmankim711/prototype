#!/usr/bin/env python3
"""
Test script to verify the 400 error fix for excel/enhanced-export endpoint
Tests both the getFields action and form export scenarios
"""

import requests
import json
import sys


def test_get_fields_action():
    """Test the getFields action that was failing"""
    url = "http://localhost:5000/api/v1/integrations/excel/enhanced-export"

    payload = {
        "dataSourceId": "mock-excel-1",
        "action": "getFields"
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🧪 Testing getFields action for mock-excel-1...")
    print(f"📡 POST {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")

        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📄 Response Body: {json.dumps(response_data, indent=2)}")

            if response.status_code == 200:
                print("✅ SUCCESS: getFields action worked!")

                # Validate response structure
                if 'fields' in response_data and isinstance(response_data['fields'], list):
                    print(f"✅ Valid response structure with {len(response_data['fields'])} fields")

                    if response_data.get('dataSourceId') == 'mock-excel-1':
                        print("✅ Correct dataSourceId returned")
                    else:
                        print("❌ Incorrect dataSourceId in response")

                    return True
                else:
                    print("❌ Invalid response structure")
                    return False
            else:
                print(f"❌ FAILED: Status {response.status_code}")

                # Check if we got enhanced error format
                if 'error' in response_data and 'request_id' in response_data:
                    print("✅ Enhanced error format detected")
                    if 'details' in response_data and 'suggestion' in response_data.get('details', {}):
                        print(f"💡 Suggestion: {response_data['details']['suggestion']}")
                else:
                    print("❌ Old error format detected")

                return False
        else:
            print(f"❌ Non-JSON response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running on localhost:5000?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def test_invalid_data_source():
    """Test with invalid dataSourceId to verify error handling"""
    url = "http://localhost:5000/api/v1/integrations/excel/enhanced-export"

    payload = {
        "dataSourceId": "invalid-data-source-123!@#",
        "action": "getFields"
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("\n🧪 Testing invalid dataSourceId...")
    print(f"📡 POST {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        print(f"📊 Status Code: {response.status_code}")

        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📄 Response Body: {json.dumps(response_data, indent=2)}")

            if response.status_code == 400:
                print("✅ Correctly returned 400 for invalid dataSourceId")

                # Check enhanced error format
                if response_data.get('code') == 'BAD_REQUEST':
                    print("✅ Enhanced error code detected")

                if 'invalid_fields' in response_data.get('details', {}):
                    print("✅ Field validation details provided")

                if 'request_id' in response_data:
                    print(f"✅ Request ID provided: {response_data['request_id']}")

                return True
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                return False
        else:
            print(f"❌ Non-JSON response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_missing_data_source():
    """Test missing dataSourceId to verify error handling"""
    url = "http://localhost:5000/api/v1/integrations/excel/enhanced-export"

    payload = {
        "action": "getFields"
        # Missing dataSourceId
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("\n🧪 Testing missing dataSourceId...")
    print(f"📡 POST {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        print(f"📊 Status Code: {response.status_code}")

        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📄 Response Body: {json.dumps(response_data, indent=2)}")

            if response.status_code == 400:
                print("✅ Correctly returned 400 for missing dataSourceId")

                # Check for missing fields error
                if 'missing_fields' in response_data.get('details', {}):
                    missing_fields = response_data['details']['missing_fields']
                    if 'dataSourceId' in missing_fields:
                        print("✅ Correctly identified missing dataSourceId")
                        return True

                return False
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                return False
        else:
            print(f"❌ Non-JSON response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_invalid_content_type():
    """Test invalid content type to verify error handling"""
    url = "http://localhost:5000/api/v1/integrations/excel/enhanced-export"

    payload = "not json"

    headers = {
        "Content-Type": "text/plain"
    }

    print("\n🧪 Testing invalid content type...")
    print(f"📡 POST {url}")
    print(f"📦 Payload: {payload}")
    print(f"🏷️ Content-Type: text/plain")

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)

        print(f"📊 Status Code: {response.status_code}")

        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📄 Response Body: {json.dumps(response_data, indent=2)}")

            if response.status_code == 400:
                print("✅ Correctly returned 400 for invalid content type")

                # Check for content type error
                if response_data.get('code') == 'INVALID_CONTENT_TYPE':
                    print("✅ Correct error code for content type")

                    details = response_data.get('details', {})
                    if 'expected_content_type' in details and 'received_content_type' in details:
                        print("✅ Content type details provided")
                        return True

                return False
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                return False
        else:
            print(f"❌ Non-JSON response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🚀 Testing 400 Error Fix for excel/enhanced-export endpoint")
    print("=" * 60)

    tests = [
        ("getFields Action (mock-excel-1)", test_get_fields_action),
        ("Invalid DataSource ID", test_invalid_data_source),
        ("Missing DataSource ID", test_missing_data_source),
        ("Invalid Content Type", test_invalid_content_type),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        success = test_func()
        results.append((test_name, success))
        print(f"Result: {'✅ PASS' if success else '❌ FAIL'}")

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if success:
            passed += 1

    print("-" * 60)
    print(f"Total: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! The 400 error fix is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the backend implementation.")
        sys.exit(1)


if __name__ == "__main__":
    main()