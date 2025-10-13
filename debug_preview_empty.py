#!/usr/bin/env python3
"""
Debug why report preview shows nothing
"""

import requests
import json
import os

def test_real_reports():
    """Find and test with real reports that exist"""
    print("🔍 Finding Real Reports in Database")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # Try to get list of reports
        response = requests.get(f"{base_url}/api/reports", timeout=5)
        print(f"GET /api/reports: Status {response.status_code}")
        
        if response.status_code == 401:
            print("🔐 Need to authenticate first. Let's try to login...")
            return test_with_auth()
        elif response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Got reports data: {type(data)}")
                
                # Handle different response formats
                reports = []
                if isinstance(data, list):
                    reports = data
                elif isinstance(data, dict):
                    reports = data.get('reports', []) or data.get('data', [])
                
                if reports:
                    print(f"📊 Found {len(reports)} reports")
                    for i, report in enumerate(reports[:3]):  # Test first 3 reports
                        print(f"\n🧪 Testing Report {i+1}:")
                        if isinstance(report, dict):
                            report_id = report.get('id') or report.get('reportId') or report.get('report_id')
                            title = report.get('title', 'Untitled')
                            print(f"   ID: {report_id}, Title: {title}")
                            
                            if report_id:
                                test_report_preview(report_id)
                        else:
                            print(f"   Unexpected report format: {report}")
                else:
                    print("❌ No reports found in database")
                    print("💡 Try generating a report first in NextGen Report Builder")
                    
            except Exception as e:
                print(f"❌ Could not parse reports response: {e}")
                print(f"Raw response: {response.text[:500]}...")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Failed to get reports: {e}")

def test_with_auth():
    """Try to get a token and test authenticated requests"""
    print("🔐 Testing with Authentication")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    
    # Try common test credentials
    test_credentials = [
        {"email": "admin@test.com", "password": "admin"},
        {"email": "test@test.com", "password": "test"},
        {"email": "user@example.com", "password": "password"},
    ]
    
    for creds in test_credentials:
        try:
            response = requests.post(f"{base_url}/api/auth/login", json=creds, timeout=5)
            print(f"Login attempt {creds['email']}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    token = data.get('access_token')
                    if token:
                        print("✅ Got access token!")
                        return test_with_token(token)
                except:
                    print("⚠️ Could not parse login response")
        except Exception as e:
            print(f"❌ Login failed: {e}")
    
    print("💡 No test credentials worked. Check if you have users in database.")
    return False

def test_with_token(token):
    """Test reports with authentication token"""
    print(f"🔐 Testing with Token: {token[:20]}...")
    print("=" * 45)
    
    base_url = "http://localhost:5000"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{base_url}/api/reports", headers=headers, timeout=5)
        print(f"GET /api/reports with token: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            reports = data if isinstance(data, list) else data.get('reports', [])
            
            if reports:
                print(f"✅ Found {len(reports)} reports")
                # Test the first real report
                for report in reports[:2]:
                    report_id = report.get('id') or report.get('reportId')
                    if report_id:
                        test_authenticated_preview(report_id, headers)
                        break
            else:
                print("❌ No reports found")
        else:
            print(f"❌ Still failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Authenticated request failed: {e}")

def test_report_preview(report_id):
    """Test preview endpoints for a specific report"""
    base_url = "http://localhost:5000"
    
    endpoints = [
        f"/api/reports/{report_id}/preview",
        f"/api/v1/nextgen/reports/{report_id}/preview",
        f"/api/excel-to-docx/{report_id}/preview"
    ]
    
    print(f"   🔍 Testing preview endpoints for report {report_id}:")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=3)
            print(f"     {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"     ✅ SUCCESS: {data}")
                    return True
                except:
                    print(f"     ✅ SUCCESS: {response.text[:100]}...")
                    return True
            elif response.status_code == 401:
                print(f"     🔐 Needs auth")
            else:
                try:
                    error = response.json()
                    print(f"     ❌ {error}")
                except:
                    print(f"     ❌ {response.text[:50]}...")
                    
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    return False

def test_authenticated_preview(report_id, headers):
    """Test preview with authentication"""
    base_url = "http://localhost:5000"
    
    endpoints = [
        f"/api/reports/{report_id}/preview",
        f"/api/v1/nextgen/reports/{report_id}/preview"
    ]
    
    print(f"🔍 Testing authenticated preview for report {report_id}:")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS!")
                    print(f"   📄 Preview data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Check what type of preview data we got
                    if isinstance(data, dict):
                        if 'preview_url' in data:
                            print(f"   🔗 Preview URL: {data['preview_url']}")
                        if 'preview_type' in data:
                            print(f"   📄 Preview type: {data['preview_type']}")
                        if 'files' in data:
                            print(f"   📁 Files: {data['files']}")
                        if 'content' in data:
                            content = str(data['content'])
                            print(f"   📝 Content preview: {content[:100]}...")
                            
                    return True
                    
                except Exception as e:
                    print(f"   ✅ SUCCESS but could not parse JSON: {e}")
                    print(f"   📄 Raw response: {response.text[:200]}...")
                    return True
                    
            else:
                try:
                    error = response.json()
                    print(f"   ❌ {error}")
                except:
                    print(f"   ❌ {response.text[:100]}...")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

def check_preview_files():
    """Check if preview files exist on disk"""
    print("\n📁 Checking Preview Files on Disk")
    print("=" * 40)
    
    preview_dirs = [
        "backend/static/previews",
        "backend/static/generated", 
        "backend/uploads",
        "backend/reports"
    ]
    
    for dir_path in preview_dirs:
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"✅ {dir_path}: {len(files)} files")
            
            # Show some example files
            for file in files[:3]:
                file_path = os.path.join(dir_path, file)
                size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                print(f"   📄 {file} ({size} bytes)")
        else:
            print(f"❌ {dir_path}: Directory not found")

if __name__ == "__main__":
    print("🐛 Debug: Why Report Preview Shows Nothing")
    print("=" * 60)
    
    test_real_reports()
    check_preview_files()
    
    print("\n💡 Common Issues & Solutions:")
    print("=" * 40)
    print("1. 🔐 User not logged in → Login first")
    print("2. 📄 Report doesn't exist → Generate a report first")
    print("3. 🎨 Preview not generated → Backend may need to create preview")
    print("4. 🌐 Frontend not displaying → Check browser console for errors")
    print("5. 📁 Preview files missing → Check file generation logic")
    
    print("\n🧪 Next Steps:")
    print("1. Generate a report in NextGen Report Builder")
    print("2. Note the report ID from the success message")
    print("3. Test preview with that specific ID")
    print("4. Check browser Network tab when clicking Preview")