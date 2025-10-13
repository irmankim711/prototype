#!/usr/bin/env python3
"""
Test AI Suggestions Endpoints Fix
Tests both AI suggestion endpoints to ensure they're working correctly
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_data_source_ai_suggestions():
    """Test the data source-based AI suggestions endpoint"""
    print("🔍 Testing data source AI suggestions endpoint...")

    url = f"{BASE_URL}/api/v1/nextgen/ai/suggestions"
    payload = {
        "dataSourceId": "test_data_source",
        "context": {
            "reportType": "business_analysis",
            "dataType": "sales_data"
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Data source AI suggestions endpoint working")
            print(f"   Response keys: {list(result.keys())}")
            return True
        elif response.status_code == 401:
            print("   ⚠️ Authentication required (expected for secured endpoint)")
            return True
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Raw response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the server running?")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_text_ai_suggestions():
    """Test the text improvement AI suggestions endpoint"""
    print("🔍 Testing text AI suggestions endpoint...")

    url = f"{BASE_URL}/api/v1/nextgen/ai/text-suggestions"
    payload = {
        "text": "This is a sample text that could be improved for better readability.",
        "context": "report"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Text AI suggestions endpoint working")
            print(f"   Response keys: {list(result.keys())}")
            return True
        elif response.status_code == 401:
            print("   ⚠️ Authentication required (expected for secured endpoint)")
            return True
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Raw response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the server running?")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_nextgen_routes():
    """Test that NextGen routes are properly registered"""
    print("🔍 Testing NextGen route registration...")

    # Test basic NextGen endpoint
    url = f"{BASE_URL}/api/v1/nextgen/cors-test"

    try:
        response = requests.get(url, timeout=5)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ NextGen blueprint properly registered")
            return True
        else:
            print(f"   ❌ NextGen blueprint issue: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the server running?")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_old_route_conflict():
    """Test that the old conflicting route doesn't exist anymore"""
    print("🔍 Testing that duplicate route conflict is resolved...")

    # This should work now (data source suggestions)
    url1 = f"{BASE_URL}/api/v1/nextgen/ai/suggestions"
    payload1 = {"dataSourceId": "test"}

    # This should work on the new route (text suggestions)
    url2 = f"{BASE_URL}/api/v1/nextgen/ai/text-suggestions"
    payload2 = {"text": "test text"}

    try:
        response1 = requests.post(url1, json=payload1, timeout=5)
        response2 = requests.post(url2, json=payload2, timeout=5)

        print(f"   /ai/suggestions status: {response1.status_code}")
        print(f"   /ai/text-suggestions status: {response2.status_code}")

        # Both should return 200 or 401 (auth required), not 404
        if response1.status_code in [200, 401] and response2.status_code in [200, 401]:
            print("   ✅ Both endpoints accessible (no 404 conflicts)")
            return True
        else:
            print("   ❌ One or both endpoints returning errors")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AI Suggestions Endpoints Fix")
    print("=" * 50)

    tests = [
        ("NextGen Routes Registration", test_nextgen_routes),
        ("Route Conflict Resolution", test_old_route_conflict),
        ("Data Source AI Suggestions", test_data_source_ai_suggestions),
        ("Text AI Suggestions", test_text_ai_suggestions),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if success:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! AI suggestions endpoints are working correctly.")
    else:
        print("⚠️  Some tests failed. The fix may need additional work.")

if __name__ == "__main__":
    main()