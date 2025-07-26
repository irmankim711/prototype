#!/usr/bin/env python3
"""
Test script for the reports history endpoint
"""

import requests
import json
import sys

def test_reports_history():
    """Test the /api/reports/history endpoint"""
    base_url = "http://localhost:5000/api"
    
    print("🔍 Testing Reports History Endpoint...")
    
    # For testing without authentication, let's first check if the endpoint exists
    try:
        response = requests.get(f"{base_url}/reports/history", timeout=5)
        
        if response.status_code == 401:
            print("✅ Endpoint exists but requires authentication (expected)")
            print("💡 To test with authentication, you need to:")
            print("   1. Register/login to get a JWT token")
            print("   2. Include the token in the Authorization header")
            return True
        elif response.status_code == 200:
            print("✅ Endpoint working and returned data")
            data = response.json()
            print(f"   Found {len(data.get('reports', []))} reports")
            return True
        elif response.status_code == 500:
            print("❌ Server error - check backend logs")
            print(f"   Response: {response.text}")
            return False
        else:
            print(f"❓ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("   Make sure the backend is running: python run.py")
        return False
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def test_all_report_endpoints():
    """Test all report-related endpoints"""
    base_url = "http://localhost:5000/api"
    endpoints = [
        "/reports",
        "/reports/history", 
        "/reports/recent"
    ]
    
    print("🚀 Testing all report endpoints...")
    print("=" * 40)
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 401:
                status = "✅ REQUIRES AUTH"
            elif response.status_code == 200:
                status = "✅ WORKING"
            elif response.status_code == 500:
                status = "❌ SERVER ERROR"
            else:
                status = f"❓ HTTP {response.status_code}"
            
            results[endpoint] = status
            print(f"{endpoint:<20} {status}")
            
        except requests.exceptions.ConnectionError:
            results[endpoint] = "❌ NO CONNECTION"
            print(f"{endpoint:<20} ❌ NO CONNECTION")
        except Exception as e:
            results[endpoint] = f"❌ ERROR: {str(e)[:30]}"
            print(f"{endpoint:<20} ❌ ERROR")
    
    print("=" * 40)
    
    # Summary
    working_count = sum(1 for status in results.values() if "✅" in status)
    total_count = len(results)
    
    print(f"📊 Summary: {working_count}/{total_count} endpoints working/accessible")
    
    return working_count == total_count

if __name__ == "__main__":
    print("Reports History Endpoint Test")
    print("=" * 30)
    
    # Test the specific history endpoint
    history_ok = test_reports_history()
    print()
    
    # Test all endpoints
    all_ok = test_all_report_endpoints()
    
    if history_ok and all_ok:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        sys.exit(1)
