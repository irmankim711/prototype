"""
Comprehensive Feature Test Suite
Tests all implemented features:
1. Chart generation (Bar, Line, Pie)
2. Report preview functionality
3. PDF/DOCX/Excel downloads
4. Data mapping
5. Complete workflow
"""

import requests
import json
import os
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v1/nextgen"
TEST_EXCEL_FILE = r"c:\Users\IRMAN\OneDrive\Desktop\prototype\Data\SENARAI SEMAK PUNCAK ALAM.xlsx"

# Test results
test_results = []

def log_test(test_name, status, message=""):
    """Log test result"""
    result = {
        "test": test_name,
        "status": status,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    test_results.append(result)
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_icon} {test_name}: {status}")
    if message:
        print(f"   {message}")

def test_backend_health():
    """Test 1: Backend Server Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            log_test("Backend Health Check", "PASS", "Server is running")
            return True
        else:
            log_test("Backend Health Check", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Backend Health Check", "FAIL", str(e))
        return False

def test_chart_generator_service():
    """Test 2: Chart Generator Service"""
    try:
        # Test if matplotlib is available
        import sys
        sys.path.insert(0, r'c:\Users\IRMAN\OneDrive\Desktop\prototype\backend')

        from app.services.chart_generator_service import chart_generator_service

        # Test data
        test_data = [
            {"name": "A", "value": 10},
            {"name": "B", "value": 20},
            {"name": "C", "value": 15}
        ]

        # Test bar chart
        try:
            config = {
                "title": "Test Bar Chart",
                "xField": "name",
                "yField": "value",
                "colors": ["#3b82f6"]
            }
            file_path, base64_data = chart_generator_service.generate_bar_chart(test_data, config)
            if file_path and os.path.exists(file_path):
                log_test("Bar Chart Generation", "PASS", f"Generated: {file_path}")
            else:
                log_test("Bar Chart Generation", "FAIL", "File not created")
        except Exception as e:
            log_test("Bar Chart Generation", "FAIL", str(e))

        # Test line chart
        try:
            config = {
                "title": "Test Line Chart",
                "xField": "name",
                "yField": "value",
                "colors": ["#10b981"]
            }
            file_path, base64_data = chart_generator_service.generate_line_chart(test_data, config)
            if file_path and os.path.exists(file_path):
                log_test("Line Chart Generation", "PASS", f"Generated: {file_path}")
            else:
                log_test("Line Chart Generation", "FAIL", "File not created")
        except Exception as e:
            log_test("Line Chart Generation", "FAIL", str(e))

        # Test pie chart
        try:
            config = {
                "title": "Test Pie Chart",
                "nameField": "name",
                "valueField": "value",
                "colors": ["#3b82f6", "#10b981", "#f59e0b"]
            }
            file_path, base64_data = chart_generator_service.generate_pie_chart(test_data, config)
            if file_path and os.path.exists(file_path):
                log_test("Pie Chart Generation", "PASS", f"Generated: {file_path}")
            else:
                log_test("Pie Chart Generation", "FAIL", "File not created")
        except Exception as e:
            log_test("Pie Chart Generation", "FAIL", str(e))

        return True
    except ImportError as e:
        log_test("Chart Generator Service", "FAIL", f"Import error: {str(e)}")
        return False
    except Exception as e:
        log_test("Chart Generator Service", "FAIL", str(e))
        return False

def test_excel_upload():
    """Test 3: Excel File Upload"""
    try:
        if not os.path.exists(TEST_EXCEL_FILE):
            log_test("Excel Upload", "SKIP", "Test file not found")
            return None

        with open(TEST_EXCEL_FILE, 'rb') as f:
            files = {'file': (os.path.basename(TEST_EXCEL_FILE), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f"{API_BASE}/excel/upload", files=files, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Extract file path from dataSource object
                    file_path = data.get('dataSource', {}).get('filePath')
                    log_test("Excel Upload", "PASS", f"Uploaded to: {file_path}")
                    return file_path
                else:
                    log_test("Excel Upload", "FAIL", data.get('error', 'Unknown error'))
                    return None
            else:
                log_test("Excel Upload", "FAIL", f"Status code: {response.status_code}")
                return None
    except Exception as e:
        log_test("Excel Upload", "FAIL", str(e))
        return None

def test_report_generation(excel_file_path):
    """Test 4: Report Generation with Charts"""
    try:
        if not excel_file_path:
            log_test("Report Generation", "SKIP", "No Excel file uploaded")
            return None

        # Prepare request with charts
        payload = {
            "excelFilePath": excel_file_path,
            "templateId": "04- LAPORAN FU _ PUNCAK ALAM_final.docx",
            "reportTitle": "Test Report with Charts",
            "charts": [
                {
                    "chartType": "bar",
                    "title": "Test Bar Chart",
                    "data": [
                        {"name": "Item 1", "value": 10},
                        {"name": "Item 2", "value": 20},
                        {"name": "Item 3", "value": 15}
                    ],
                    "xField": "name",
                    "yField": "value"
                },
                {
                    "chartType": "pie",
                    "title": "Test Pie Chart",
                    "data": [
                        {"name": "Category A", "value": 30},
                        {"name": "Category B", "value": 45},
                        {"name": "Category C", "value": 25}
                    ],
                    "nameField": "name",
                    "valueField": "value"
                }
            ],
            "images": []
        }

        response = requests.post(
            f"{API_BASE}/excel/generate-report",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # API returns reportId in camelCase
                report_id = data.get('reportId') or data.get('report', {}).get('id')
                log_test("Report Generation", "PASS", f"Report ID: {report_id}")
                return report_id
            else:
                log_test("Report Generation", "FAIL", data.get('error', 'Unknown error'))
                return None
        else:
            log_test("Report Generation", "FAIL", f"Status code: {response.status_code}, Response: {response.text[:200]}")
            return None
    except Exception as e:
        log_test("Report Generation", "FAIL", str(e))
        return None

def test_report_preview(report_id):
    """Test 5: Report Preview"""
    try:
        if not report_id:
            log_test("Report Preview", "SKIP", "No report generated")
            return False

        response = requests.get(f"{API_BASE}/reports/{report_id}/preview", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                log_test("Report Preview", "PASS", "Preview data retrieved")
                return True
            else:
                log_test("Report Preview", "FAIL", "No success in response")
                return False
        else:
            log_test("Report Preview", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Report Preview", "FAIL", str(e))
        return False

def test_download_endpoints(report_id):
    """Test 6: Download Endpoints (PDF, DOCX, Excel)"""
    try:
        if not report_id:
            log_test("Download Endpoints", "SKIP", "No report generated")
            return False

        formats = ["pdf", "docx", "excel"]
        all_passed = True

        for fmt in formats:
            try:
                response = requests.get(
                    f"{API_BASE}/reports/{report_id}/download/{fmt}",
                    timeout=30,
                    stream=True
                )

                if response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    log_test(f"Download {fmt.upper()}", "PASS", f"Content-Type: {content_type}")
                else:
                    log_test(f"Download {fmt.upper()}", "FAIL", f"Status code: {response.status_code}")
                    all_passed = False
            except Exception as e:
                log_test(f"Download {fmt.upper()}", "FAIL", str(e))
                all_passed = False

        return all_passed
    except Exception as e:
        log_test("Download Endpoints", "FAIL", str(e))
        return False

def test_data_mapping():
    """Test 7: Data Mapping Service"""
    try:
        import sys
        sys.path.insert(0, r'c:\Users\IRMAN\OneDrive\Desktop\prototype\backend')

        from app.services.template_data_mapper import template_data_mapper

        # Test data
        raw_data = {
            'records': [
                {
                    'NAMA': 'Test User 1',
                    'MARKAH_PRE': '70',
                    'MARKAH_POST': '85',
                    'IC': '123456789012',
                    'Phone': '0123456789'
                },
                {
                    'NAMA': 'Test User 2',
                    'MARKAH_PRE': '65',
                    'MARKAH_POST': '80',
                    'IC': '987654321098',
                    'Phone': '0987654321'
                }
            ],
            'metadata': {
                'file_path': 'test.xlsx',
                'record_count': 2
            }
        }

        # Test mapping
        mapped_data = template_data_mapper.map_data_for_template(raw_data, 'Test.docx')

        if mapped_data and 'participants' in mapped_data:
            log_test("Data Mapping", "PASS", f"Mapped {len(mapped_data['participants'])} records")
            return True
        else:
            log_test("Data Mapping", "FAIL", f"No participants in mapped data. Keys: {list(mapped_data.keys()) if mapped_data else 'None'}")
            return False
    except Exception as e:
        log_test("Data Mapping", "FAIL", str(e))
        return False

def generate_report():
    """Generate test report"""
    print("\n" + "="*70)
    print("📊 COMPREHENSIVE FEATURE TEST REPORT")
    print("="*70 + "\n")

    print(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Tests: {len(test_results)}\n")

    # Count results
    passed = sum(1 for r in test_results if r['status'] == 'PASS')
    failed = sum(1 for r in test_results if r['status'] == 'FAIL')
    skipped = sum(1 for r in test_results if r['status'] == 'SKIP')

    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")

    print("\n" + "="*70)
    print("DETAILED RESULTS")
    print("="*70 + "\n")

    for result in test_results:
        status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result['message']:
            print(f"   → {result['message']}")
        print(f"   ⏰ {result['timestamp']}\n")

    # Save to JSON
    with open('test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)

    print("="*70)
    print(f"📝 Detailed results saved to: test_results.json")
    print("="*70)

def main():
    """Main test runner"""
    print("\n🚀 Starting Comprehensive Feature Tests...\n")

    # Test 1: Backend Health
    print("\n" + "-"*70)
    print("TEST 1: Backend Server Health")
    print("-"*70)
    backend_ok = test_backend_health()

    if not backend_ok:
        print("\n⚠️  Backend not running. Please start the backend server first.")
        print("   Run: cd backend && python run.py")
        generate_report()
        return

    # Test 2: Chart Generation
    print("\n" + "-"*70)
    print("TEST 2: Chart Generator Service")
    print("-"*70)
    test_chart_generator_service()

    # Test 3: Excel Upload
    print("\n" + "-"*70)
    print("TEST 3: Excel File Upload")
    print("-"*70)
    excel_file_path = test_excel_upload()

    # Test 4: Report Generation
    print("\n" + "-"*70)
    print("TEST 4: Report Generation with Charts")
    print("-"*70)
    report_id = test_report_generation(excel_file_path)

    # Test 5: Report Preview
    print("\n" + "-"*70)
    print("TEST 5: Report Preview")
    print("-"*70)
    test_report_preview(report_id)

    # Test 6: Download Endpoints
    print("\n" + "-"*70)
    print("TEST 6: Download Endpoints")
    print("-"*70)
    test_download_endpoints(report_id)

    # Test 7: Data Mapping
    print("\n" + "-"*70)
    print("TEST 7: Data Mapping Service")
    print("-"*70)
    test_data_mapping()

    # Generate report
    generate_report()

if __name__ == "__main__":
    main()
