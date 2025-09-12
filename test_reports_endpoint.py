#!/usr/bin/env python3
"""
Test script to debug the reports endpoint issue
"""
import requests
import json

def test_reports_endpoint():
    """Test the reports endpoint to see what error occurs"""
    try:
        print("🔍 Testing reports endpoint...")
        
        # Test the reports endpoint
        response = requests.get("http://localhost:5000/api/reports")
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Reports endpoint working!")
            data = response.json()
            print(f"📄 Reports data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Reports endpoint failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"🚨 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"🚨 Raw error response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_health_endpoint():
    """Test the health endpoint to verify backend is running"""
    try:
        print("\n🔍 Testing health endpoint...")
        
        response = requests.get("http://localhost:5000/health")
        
        if response.status_code == 200:
            print("✅ Health endpoint working!")
            data = response.json()
            print(f"📊 Backend status: {data.get('status', 'unknown')}")
            print(f"🗄️ Database status: {data.get('database', 'unknown')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Reports Endpoint Debug Test")
    print("=" * 50)
    
    test_health_endpoint()
    test_reports_endpoint()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed")
