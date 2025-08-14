#!/usr/bin/env python3
"""
Quick test to measure server response times
"""
import time
import requests

def test_server_speeds():
    print("🔌 Testing Server Response Times...")
    
    # Test frontend
    try:
        frontend_start = time.time()
        response = requests.get("http://localhost:5173", timeout=5)
        frontend_time = (time.time() - frontend_start) * 1000
        
        if response.status_code == 200:
            print(f"✅ Frontend: {response.status_code} ({frontend_time:.0f}ms)")
        else:
            print(f"⚠️  Frontend: {response.status_code} ({frontend_time:.0f}ms)")
    except Exception as e:
        print(f"❌ Frontend failed: {e}")
    
    # Test backend health
    try:
        backend_start = time.time()
        response = requests.get("http://localhost:5000", timeout=5)
        backend_time = (time.time() - backend_start) * 1000
        
        if response.status_code in [200, 404]:  # 404 is fine for root endpoint
            print(f"✅ Backend: {response.status_code} ({backend_time:.0f}ms)")
        else:
            print(f"⚠️  Backend: {response.status_code} ({backend_time:.0f}ms)")
    except Exception as e:
        print(f"❌ Backend failed: {e}")

def test_critical_endpoints():
    print("\n🎯 Testing Critical Form Builder Endpoints...")
    
    # Test endpoints that FormBuilder uses
    endpoints = [
        "/api/forms/field-types",
        "/api/forms/",
    ]
    
    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 401:
                print(f"🔒 {endpoint}: Auth required ({response_time:.0f}ms)")
            elif response.status_code == 200:
                print(f"✅ {endpoint}: Success ({response_time:.0f}ms)")
            else:
                print(f"⚠️  {endpoint}: {response.status_code} ({response_time:.0f}ms)")
                
            # Check if response is too slow
            if response_time > 2000:
                print(f"   🐌 SLOW: This endpoint is causing buffering!")
                
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def main():
    print("🚀 Speed Test for Form Builder Performance")
    print("=" * 50)
    
    test_server_speeds()
    test_critical_endpoints()
    
    print("\n💡 Performance Tips:")
    print("   - Frontend should respond in < 100ms")
    print("   - Backend should respond in < 500ms") 
    print("   - API endpoints over 1000ms cause buffering")
    print("   - Our optimizations use fallbacks to avoid slow APIs")

if __name__ == "__main__":
    main()
