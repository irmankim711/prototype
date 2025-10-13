#!/usr/bin/env python3
"""
Debug Preview Issue - Analyze the cascading preview endpoint failures
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app import create_app, db
    from app.models import Report, User
    from app.services.convertapi_service import convertapi_service
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def debug_report_16():
    """Debug Report ID 16 specifically"""
    print("🔍 DEBUGGING REPORT ID 16")
    print("=" * 50)

    with create_app().app_context():
        # Check if report exists
        report = Report.query.get(16)
        if not report:
            print("❌ Report ID 16 not found in database")
            return False

        print(f"✅ Report 16 exists:")
        print(f"   - Title: {report.title}")
        print(f"   - Status: {report.status}")
        print(f"   - User ID: {report.user_id}")
        print(f"   - Created: {report.created_at}")
        print(f"   - File path: {report.file_path}")
        print(f"   - Template ID: {report.template_id}")
        print(f"   - Generation progress: {report.generation_progress}")

        # Check files
        if hasattr(report, 'files') and report.files:
            print(f"   - Associated files: {len(report.files)}")
            for file in report.files:
                file_exists = os.path.exists(file.file_path) if file.file_path else False
                print(f"     * {file.filename} - {file.file_type} - Exists: {file_exists}")
        else:
            print("   - No associated files")

        return True

def test_convertapi_connection():
    """Test ConvertAPI service connection"""
    print("\n🔌 TESTING CONVERTAPI CONNECTION")
    print("=" * 50)

    # Check environment variable
    api_key = os.getenv('convertAPI')
    if not api_key:
        print("❌ ConvertAPI key not found in environment")
        return False

    print(f"✅ ConvertAPI key found: {api_key[:10]}...")

    # Test connection
    result = convertapi_service.test_connection()
    if result['success']:
        print("✅ ConvertAPI connection successful")
        if 'user_info' in result:
            print(f"   - User info: {result['user_info']}")
    else:
        print(f"❌ ConvertAPI connection failed: {result['error']}")
        return False

    return True

def test_preview_endpoints():
    """Test the preview endpoints directly"""
    print("\n🌐 TESTING PREVIEW ENDPOINTS")
    print("=" * 50)

    base_url = "http://localhost:5000"
    report_id = 16

    endpoints = [
        f"/api/reports/{report_id}/preview",
        f"/api/excel-to-pdf/preview/{report_id}",
        f"/api/v1/nextgen/reports/{report_id}/export?format=pdf"
    ]

    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n🔗 Testing: {url}")

            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ Success")
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"   ❌ Error: {response.text[:200]}")

        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed - Backend not running on port 5000")
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")

def analyze_frontend_config():
    """Analyze frontend configuration for port issues"""
    print("\n⚙️ ANALYZING FRONTEND CONFIGURATION")
    print("=" * 50)

    # Check vite config
    vite_config_path = "frontend/vite.config.ts"
    if os.path.exists(vite_config_path):
        print(f"✅ Found Vite config: {vite_config_path}")
        with open(vite_config_path, 'r') as f:
            content = f.read()
            if 'proxy' in content:
                print("   - Proxy configuration found")
                # Extract proxy lines
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'proxy' in line.lower() or 'target' in line:
                        print(f"   {i+1}: {line.strip()}")
            else:
                print("   - No proxy configuration found")

    # Check package.json for dev server config
    package_json_path = "frontend/package.json"
    if os.path.exists(package_json_path):
        print(f"✅ Found package.json: {package_json_path}")
        with open(package_json_path, 'r') as f:
            try:
                data = json.load(f)
                if 'scripts' in data:
                    dev_script = data['scripts'].get('dev', 'Not found')
                    print(f"   - Dev script: {dev_script}")
            except json.JSONDecodeError:
                print("   - Error reading package.json")

def main():
    """Main debugging function"""
    print("🚨 CASCADING PREVIEW ENDPOINT FAILURES - DEBUG ANALYSIS")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Check Report ID 16
    report_exists = debug_report_16()

    # 2. Test ConvertAPI
    convertapi_working = test_convertapi_connection()

    # 3. Test endpoints
    test_preview_endpoints()

    # 4. Analyze frontend config
    analyze_frontend_config()

    # Summary
    print("\n📋 SUMMARY")
    print("=" * 50)
    print(f"Report 16 exists: {'✅' if report_exists else '❌'}")
    print(f"ConvertAPI working: {'✅' if convertapi_working else '❌'}")
    print("\n🔧 RECOMMENDATIONS:")

    if not report_exists:
        print("- Report ID 16 doesn't exist - check if it was deleted or ID is wrong")

    if not convertapi_working:
        print("- Fix ConvertAPI configuration in backend/.env")
        print("- Verify convertAPI key is valid")

    print("- Ensure backend is running on port 5000")
    print("- Check frontend proxy configuration for correct backend port")
    print("- Verify route registration in Flask application")

if __name__ == "__main__":
    main()