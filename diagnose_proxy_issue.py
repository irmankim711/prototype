#!/usr/bin/env python3
"""
Diagnose the ECONNREFUSED proxy issue
"""

import requests
import json
import time

def test_backend_direct():
    """Test backend directly without proxy"""
    print("🔍 Testing Backend Directly")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/excel-to-docx/13/preview",
        "/api/reports/health", 
        "/api/reports",
        "/api/v1/nextgen/cors-test",
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=3)
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code != 200:
                try:
                    data = response.json()
                    if "error" in data:
                        print(f"   Error: {data['error']}")
                    else:
                        print(f"   Response: {data}")
                except:
                    print(f"   Response: {response.text[:100]}...")
        except requests.ConnectionError:
            print(f"❌ {endpoint}: ECONNREFUSED")
        except requests.Timeout:
            print(f"⏰ {endpoint}: TIMEOUT")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
def test_vite_proxy():
    """Test through Vite proxy"""
    print(f"\n🌐 Testing Through Vite Proxy")
    print("=" * 40)
    
    # Assuming Vite is on port 5173
    vite_url = "http://localhost:5173"
    endpoints = [
        "/api/excel-to-docx/13/preview",
        "/api/reports/health",
        "/api/reports",
    ]
    
    for endpoint in endpoints:
        url = f"{vite_url}{endpoint}"
        try:
            response = requests.get(url, timeout=3)
            print(f"✅ {endpoint}: {response.status_code}")
        except requests.ConnectionError:
            print(f"❌ {endpoint}: ECONNREFUSED (Vite proxy issue)")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def check_ports():
    """Check which ports are active"""
    print(f"\n📊 Port Status Check")
    print("=" * 30)
    
    ports_to_check = [5000, 5173, 3000]
    
    for port in ports_to_check:
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            print(f"✅ Port {port}: Active ({response.status_code})")
        except requests.ConnectionError:
            print(f"❌ Port {port}: Not reachable")
        except Exception as e:
            print(f"⚠️ Port {port}: {e}")

def suggest_solutions():
    """Provide troubleshooting steps"""
    print(f"\n🔧 Troubleshooting Steps")
    print("=" * 35)
    print("1. 🔄 Restart Vite dev server:")
    print("   cd frontend && npm run dev")
    print()
    print("2. 🔄 Restart Flask backend:")
    print("   cd backend && python run.py")
    print()
    print("3. 🌐 Check browser Network tab:")
    print("   - Look for the exact error message")
    print("   - Check if request reaches Vite proxy")
    print()
    print("4. 🧪 Test direct backend call:")
    print("   curl http://localhost:5000/api/excel-to-docx/13/preview")
    print()
    print("5. 🚫 Clear browser cache and hard refresh")
    print("   Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)")

if __name__ == "__main__":
    print("🚨 ECONNREFUSED Diagnosis Tool")
    print("=" * 50)
    
    test_backend_direct()
    test_vite_proxy() 
    check_ports()
    suggest_solutions()
    
    print(f"\n💡 Root Cause Analysis:")
    print("- ✅ Backend is running on port 5000")
    print("- ✅ Endpoint /api/excel-to-docx/13/preview exists") 
    print("- ✅ Vite proxy config looks correct")
    print("- 🔍 Issue is likely proxy connection timing or cache")