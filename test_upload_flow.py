#!/usr/bin/env python3
"""
Test the complete upload and report generation flow
"""

import requests
import json
import io

def test_upload_and_generate_flow():
    """Test the complete flow from upload to report generation"""
    print("🧪 TESTING UPLOAD AND REPORT GENERATION FLOW")
    print("=" * 60)

    base_url = "http://localhost:5000"

    # Use an existing Excel file
    excel_file_path = "C:\\Users\\IRMAN\\OneDrive\\Desktop\\prototype\\backend\\uploads\\test_simple.xlsx"

    try:
        with open(excel_file_path, 'rb') as f:
            test_excel_content = f.read()
    except FileNotFoundError:
        print(f"❌ Test Excel file not found: {excel_file_path}")
        return False

    # Step 1: Test Upload
    print("\n📤 STEP 1: Testing Excel Upload")
    print("-" * 40)

    files = {
        'file': ('test_simple.xlsx', test_excel_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }

    try:
        upload_response = requests.post(
            f"{base_url}/api/v1/nextgen/excel/upload",
            files=files,
            headers={'Authorization': 'Bearer fake-token'},
            timeout=30
        )

        print(f"Upload Status: {upload_response.status_code}")
        print(f"Upload Response: {upload_response.text[:500]}...")

        if upload_response.status_code == 200:
            upload_data = upload_response.json()

            if upload_data.get('success') and upload_data.get('dataSource'):
                file_path = upload_data['dataSource'].get('filePath')
                print(f"✅ Upload successful!")
                print(f"📁 File Path: {file_path}")

                # Step 2: Test Report Generation with the returned file path
                print("\n📊 STEP 2: Testing Report Generation")
                print("-" * 40)

                generate_payload = {
                    "excelFilePath": file_path,
                    "templateId": "1",
                    "reportTitle": "Test Report"
                }

                generate_response = requests.post(
                    f"{base_url}/api/v1/nextgen/excel/generate-report",
                    json=generate_payload,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer fake-token'
                    },
                    timeout=30
                )

                print(f"Generate Status: {generate_response.status_code}")
                print(f"Generate Response: {generate_response.text[:500]}...")

                if generate_response.status_code == 200:
                    generate_data = generate_response.json()

                    if generate_data.get('success') and generate_data.get('reportId'):
                        print(f"✅ Report generation successful!")
                        print(f"📄 Report ID: {generate_data['reportId']}")
                        print(f"📋 Report Title: {generate_data.get('reportTitle')}")
                        return True
                    else:
                        print(f"❌ Report generation failed: No reportId in response")
                        print(f"Response keys: {list(generate_data.keys()) if generate_data else 'No data'}")
                        return False
                else:
                    print(f"❌ Report generation failed with status {generate_response.status_code}")
                    return False
            else:
                print(f"❌ Upload failed: No dataSource in response")
                return False
        else:
            print(f"❌ Upload failed with status {upload_response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Backend not running")
        return False
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    success = test_upload_and_generate_flow()

    print(f"\n📋 FINAL RESULT")
    print("=" * 60)
    if success:
        print("✅ UPLOAD AND REPORT GENERATION FLOW WORKING!")
        print("The issue is likely elsewhere in the frontend handling.")
    else:
        print("❌ FLOW HAS ISSUES - Backend problem identified")

    return success

if __name__ == "__main__":
    main()