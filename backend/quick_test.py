#!/usr/bin/env python3
"""
Quick backend health check and basic functionality test
"""

import requests
import json
import sys

def test_backend():
    base_url = "http://localhost:5000"
    
    print("🔍 Testing Backend Health...")
    
    # Test 1: Basic server health - check if server responds
    try:
        response = requests.get(f"{base_url}/api/mvp/templates/list", timeout=5)
        if response.status_code in [200, 401]:  # 401 is also OK, means server is running
            print("✅ Backend server is running")
            if response.status_code == 200:
                print(f"   Templates endpoint accessible")
            else:
                print(f"   Templates endpoint requires authentication (normal)")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("   Make sure the backend is running: python run.py")
        return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False
    
    # Test 2: MVP Templates endpoint
    try:
        response = requests.get(f"{base_url}/api/mvp/templates/list", timeout=5)
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Templates endpoint working - found {len(templates)} templates")
            for template in templates:
                print(f"   - {template.get('name', template.get('filename'))}")
        else:
            print(f"❌ Templates endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Templates endpoint error: {e}")
        return False
    
    # Test 3: Preview endpoint (if templates exist)
    if templates:
        try:
            template_name = templates[0]['filename']
            test_data = {"name": "Test User", "date": "2025-07-26"}
            
            response = requests.post(
                f"{base_url}/api/mvp/templates/{template_name}/preview",
                json={"data": test_data},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'preview' in result:
                    print(f"✅ Preview generation working")
                else:
                    print(f"❌ Preview response missing 'preview' field")
                    return False
            else:
                print(f"❌ Preview generation failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
        except Exception as e:
            print(f"❌ Preview generation error: {e}")
            return False
    
    print("\n🎉 All basic tests passed! Backend is working correctly.")
    return True

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)
