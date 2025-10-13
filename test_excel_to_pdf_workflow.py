#!/usr/bin/env python3
"""
Test Excel-to-PDF Workflow
Tests the complete Excel upload and PDF report generation workflow
"""

import requests
import os
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
TEST_EXCEL_FILE = "test_data.xlsx"

def create_test_excel_file():
    """Create a simple test Excel file"""
    try:
        import pandas as pd

        # Create sample data
        data = {
            'Name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'Age': [25, 30, 35, 28, 32],
            'Department': ['Sales', 'Marketing', 'Engineering', 'Sales', 'Engineering'],
            'Salary': [50000, 60000, 80000, 55000, 75000],
            'Performance Score': [8.5, 7.2, 9.1, 8.0, 8.8]
        }

        df = pd.DataFrame(data)

        # Save to Excel file
        df.to_excel(TEST_EXCEL_FILE, index=False)
        print(f"✅ Created test Excel file: {TEST_EXCEL_FILE}")
        return True

    except ImportError:
        print("❌ pandas not available. Please create a test Excel file manually.")
        return False

def test_convertapi_connection():
    """Test ConvertAPI connection"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/excel-to-pdf/convert-test",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ ConvertAPI connection: {result.get('message', 'OK')}")
            return True
        else:
            print(f"❌ ConvertAPI connection failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ ConvertAPI test failed: {e}")
        return False

def test_supported_formats():
    """Test supported formats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/excel-to-pdf/supported-formats")

        if response.status_code == 200:
            result = response.json()
            print("✅ Supported formats retrieved:")
            print(f"   Input formats: {len(result.get('input_formats', []))}")
            print(f"   Output formats: {len(result.get('output_formats', []))}")
            print(f"   Templates: {len(result.get('templates', []))}")
            return True
        else:
            print(f"❌ Supported formats test failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Supported formats test failed: {e}")
        return False

def test_excel_to_pdf_upload():
    """Test Excel file upload and PDF generation"""
    if not os.path.exists(TEST_EXCEL_FILE):
        print(f"❌ Test file {TEST_EXCEL_FILE} not found")
        return False

    try:
        # Prepare the file for upload
        with open(TEST_EXCEL_FILE, 'rb') as f:
            files = {'file': (TEST_EXCEL_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'title': 'Test Report - Employee Data Analysis',
                'formats': 'docx,pdf',
                'template': 'excel_analysis'
            }

            print("📤 Uploading Excel file and generating report...")

            response = requests.post(
                f"{BASE_URL}/api/excel-to-pdf/upload-and-generate",
                files=files,
                data=data,
                timeout=120  # 2 minutes timeout for file processing
            )

        if response.status_code == 201:
            result = response.json()
            print("✅ Report generation successful!")
            print(f"   Report ID: {result.get('report_id')}")
            print(f"   Title: {result.get('title')}")
            print(f"   Formats: {list(result.get('formats', {}).keys())}")

            # Test download URLs
            formats = result.get('formats', {})
            for format_name, format_data in formats.items():
                download_url = format_data.get('url')
                if download_url:
                    print(f"   📥 {format_name.upper()} download: {download_url}")

            return True

        elif response.status_code == 401:
            print("❌ Authentication required. Please check Firebase token.")
            return False
        else:
            try:
                error_data = response.json()
                print(f"❌ Report generation failed: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Report generation failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

def test_health_check():
    """Test application health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Application health: {result.get('status')}")
            print(f"   Database: {result.get('database')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Excel-to-PDF Workflow")
    print("=" * 50)

    tests = [
        ("Health Check", test_health_check),
        ("Supported Formats", test_supported_formats),
        ("ConvertAPI Connection", test_convertapi_connection),
        ("Create Test Excel File", create_test_excel_file),
        ("Excel to PDF Upload", test_excel_to_pdf_upload),
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
        print("🎉 All tests passed! Excel-to-PDF workflow is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and server.")

    # Cleanup
    if os.path.exists(TEST_EXCEL_FILE):
        try:
            os.remove(TEST_EXCEL_FILE)
            print(f"🧹 Cleaned up test file: {TEST_EXCEL_FILE}")
        except:
            pass

if __name__ == "__main__":
    main()