#!/usr/bin/env python3
"""
Test ConvertAPI Integration and Preview Flow
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
    from app.models import Report
    from app.services.convertapi_service import convertapi_service
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_convertapi_functionality():
    """Test ConvertAPI service functionality"""
    print("🔌 TESTING CONVERTAPI FUNCTIONALITY")
    print("=" * 50)

    # Test connection
    connection_result = convertapi_service.test_connection()
    print(f"Connection test: {'✅ PASS' if connection_result['success'] else '❌ FAIL'}")
    if not connection_result['success']:
        print(f"   Error: {connection_result['error']}")
        return False

    # Test basic functionality
    if hasattr(convertapi_service, 'get_service_info'):
        info = convertapi_service.get_service_info()
        print(f"Service info: {info}")
    else:
        print("Service info: Available (method not exposed)")
        print(f"   API Key configured: {'✅' if convertapi_service.api_key else '❌'}")

    return True

def test_report_status_fix():
    """Test that Report ID 16 now has correct status"""
    print("\n📊 TESTING REPORT STATUS FIX")
    print("=" * 50)

    with create_app().app_context():
        report = Report.query.get(16)
        if not report:
            print("❌ Report ID 16 still not found")
            return False

        print(f"Report 16 status check:")
        print(f"   - generation_status: {report.generation_status}")
        print(f"   - status (computed): {report.status}")
        print(f"   - file_path: {report.file_path}")
        print(f"   - file_size: {report.file_size}")
        print(f"   - created_by: {report.created_by}")
        print(f"   - user_id (computed): {report.user_id}")

        # Check if it meets preview requirements
        if report.status == 'completed' and report.file_path:
            print("✅ Report meets preview requirements")
            return True
        else:
            print("❌ Report still doesn't meet preview requirements")
            return False

def test_preview_endpoints():
    """Test preview endpoints with the fixed report"""
    print("\n🌐 TESTING PREVIEW ENDPOINTS AFTER FIX")
    print("=" * 50)

    base_url = "http://localhost:5000"
    report_id = 16

    # Test the main preview endpoint
    try:
        url = f"{base_url}/api/reports/{report_id}/preview"
        print(f"🔗 Testing: {url}")

        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Preview endpoint now works!")
            try:
                data = response.json()
                print(f"   Response keys: {list(data.keys())}")
                if 'file_path' in data:
                    print(f"   File path: {data['file_path']}")
            except:
                print(f"   Response: {response.text[:200]}...")
            return True
        else:
            print(f"   ❌ Still failing: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"   ❌ Backend not running on port 5000")
        return False
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
        return False

def create_test_report():
    """Create a new test report with proper status and file_path"""
    print("\n📝 CREATING TEST REPORT WITH CORRECT FIELDS")
    print("=" * 50)

    with create_app().app_context():
        try:
            # Create a test report with all the correct fields
            test_report = Report(
                title="Test Report - ConvertAPI Integration",
                description="Test report created to verify preview functionality",
                report_type="test",
                generation_status="completed",  # This is the correct field
                generated_at=datetime.utcnow(),
                file_path="/path/to/test/report.pdf",  # Fake path for testing
                file_size=1024,
                file_format="pdf",
                download_url="/static/generated/test_report.pdf",
                created_by="test_user",
                data_source=json.dumps({"test": "data"}),
                generation_config=json.dumps({"test": "config"}),
                program_id=1,
                template_id=1
            )

            db.session.add(test_report)
            db.session.commit()

            print(f"✅ Test report created with ID: {test_report.id}")
            print(f"   - status: {test_report.status}")
            print(f"   - generation_status: {test_report.generation_status}")
            print(f"   - file_path: {test_report.file_path}")

            return test_report.id

        except Exception as e:
            print(f"❌ Failed to create test report: {e}")
            db.session.rollback()
            return None

def main():
    """Main test function"""
    print("🧪 CONVERTAPI AND PREVIEW INTEGRATION TEST")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Test ConvertAPI functionality
    convertapi_works = test_convertapi_functionality()

    # 2. Test report status fix
    report_status_fixed = test_report_status_fix()

    # 3. Create a test report with correct fields
    test_report_id = create_test_report()

    # 4. Test preview endpoints
    preview_works = test_preview_endpoints()

    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 50)
    print(f"ConvertAPI working: {'✅' if convertapi_works else '❌'}")
    print(f"Report 16 status fixed: {'✅' if report_status_fixed else '❌'}")
    print(f"Test report created: {'✅' if test_report_id else '❌'}")
    print(f"Preview endpoint working: {'✅' if preview_works else '❌'}")

    print("\n🔧 SOLUTION STATUS:")
    if all([convertapi_works, report_status_fixed, preview_works]):
        print("✅ ALL ISSUES RESOLVED! Preview system should now work.")
    else:
        print("❌ Some issues remain:")
        if not convertapi_works:
            print("   - ConvertAPI configuration needs fixing")
        if not report_status_fixed:
            print("   - Report status fields need correction")
        if not preview_works:
            print("   - Preview endpoint still has issues")

if __name__ == "__main__":
    main()