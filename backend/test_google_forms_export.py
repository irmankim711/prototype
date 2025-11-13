"""
Test script to debug Google Forms export issue
"""
import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.form_data_export_service import form_data_export_service

# Test data matching the structure from logs
test_form_id = "1yxEBr9G_test"
test_responses = [
    {
        'responseId': 'resp1',
        'createTime': '2025-11-10T07:00:00Z',
        'answers': {
            'q1': {'textAnswer': {'value': 'Answer 1'}},
            'q2': {'textAnswer': {'value': 'Answer 2'}},
        }
    },
    {
        'responseId': 'resp2',
        'createTime': '2025-11-10T07:05:00Z',
        'answers': {
            'q1': {'textAnswer': {'value': 'Answer 3'}},
            'q2': {'textAnswer': {'value': 'Answer 4'}},
        }
    }
]

test_form_info = {
    'title': 'Test Google Form',
    'questions': [
        {'questionId': 'q1', 'title': 'Question 1'},
        {'questionId': 'q2', 'title': 'Question 2'},
    ]
}

print("=" * 60)
print("Google Forms Export Test")
print("=" * 60)
print(f"Export folder: {form_data_export_service.export_folder}")
print(f"Folder exists: {os.path.exists(form_data_export_service.export_folder)}")
print(f"Current working directory: {os.getcwd()}")
print()

# Test the export
print("Testing export to Excel...")
try:
    result = form_data_export_service.export_google_form_responses(
        google_form_id=test_form_id,
        form_responses=test_responses,
        form_info=test_form_info,
        export_format='excel',
        options={}
    )

    print(f"\nExport Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Message: {result.get('message', 'N/A')}")
    print(f"  File Path: {result.get('file_path', 'N/A')}")
    print(f"  File Size: {result.get('file_size', 0)} bytes")
    print(f"  Download URL: {result.get('download_url', 'N/A')}")
    print(f"  Responses Count: {result.get('responses_count', 0)}")

    # Verify file exists
    file_path = result.get('file_path')
    if file_path:
        print(f"\nFile verification:")
        print(f"  File exists: {os.path.exists(file_path)}")
        if os.path.exists(file_path):
            print(f"  Actual file size: {os.path.getsize(file_path)} bytes")
            print(f"  File readable: {os.access(file_path, os.R_OK)}")

    # List files in export folder
    print(f"\nFiles in export folder:")
    if os.path.exists(form_data_export_service.export_folder):
        files = os.listdir(form_data_export_service.export_folder)
        if files:
            for f in files:
                full_path = os.path.join(form_data_export_service.export_folder, f)
                size = os.path.getsize(full_path)
                print(f"  - {f} ({size} bytes)")
        else:
            print("  (empty)")
    else:
        print("  (folder does not exist)")

except Exception as e:
    print(f"Error during export: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
