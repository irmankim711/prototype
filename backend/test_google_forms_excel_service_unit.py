"""
Unit test for Google Forms Excel Service
Tests the service functionality without requiring server or external APIs
"""

import os
import sys
import tempfile
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def create_mock_google_forms_data():
    """Create mock Google Forms data for testing"""

    mock_form_info = {
        'id': 'test_form_123',
        'title': 'Sample Survey Form',
        'description': 'A test survey form for demo purposes',
        'published_url': 'https://forms.gle/test123',
        'total_questions': 3,
        'form_type': 'Google Form'
    }

    mock_responses = [
        {
            'response_id': 'resp_001',
            'create_time': '2024-01-15T10:30:00Z',
            'last_submitted_time': '2024-01-15T10:30:00Z',
            'answers': {
                'What is your name?': 'John Doe',
                'How satisfied are you with our service?': '5',
                'Any additional comments?': 'Great service, very satisfied!'
            }
        },
        {
            'response_id': 'resp_002',
            'create_time': '2024-01-15T14:20:00Z',
            'last_submitted_time': '2024-01-15T14:20:00Z',
            'answers': {
                'What is your name?': 'Jane Smith',
                'How satisfied are you with our service?': '4',
                'Any additional comments?': 'Good but could be improved'
            }
        },
        {
            'response_id': 'resp_003',
            'create_time': '2024-01-16T09:15:00Z',
            'last_submitted_time': '2024-01-16T09:15:00Z',
            'answers': {
                'What is your name?': 'Bob Johnson',
                'How satisfied are you with our service?': '3',
                'Any additional comments?': ''
            }
        }
    ]

    mock_analysis = {
        'completion_stats': {
            'total_responses': 3,
            'completion_rate': 100.0,
            'first_response': '2024-01-15T10:30:00Z',
            'last_response': '2024-01-16T09:15:00Z'
        },
        'field_analysis': {
            'How satisfied are you with our service?': {
                'type': 'rating',
                'values': [5, 4, 3],
                'statistics': {
                    'mean': 4.0,
                    'median': 4.0,
                    'min': 3,
                    'max': 5,
                    'count': 3
                }
            },
            'Any additional comments?': {
                'type': 'feedback',
                'responses': ['Great service, very satisfied!', 'Good but could be improved', ''],
                'word_count': 12
            }
        }
    }

    mock_questions = {
        'question_001': {
            'title': 'What is your name?',
            'type': 'text',
            'required': True
        },
        'question_002': {
            'title': 'How satisfied are you with our service?',
            'type': 'scale',
            'required': True
        },
        'question_003': {
            'title': 'Any additional comments?',
            'type': 'text',
            'required': False
        }
    }

    return {
        'success': True,
        'form_info': mock_form_info,
        'responses': mock_responses,
        'analysis': mock_analysis,
        'questions': mock_questions,
        'data_source': 'mock_google_forms_api',
        'retrieved_at': datetime.now().isoformat()
    }

def test_google_forms_excel_service():
    """Test the Google Forms Excel service functionality"""

    print("=" * 60)
    print("Google Forms Excel Service Unit Test")
    print("=" * 60)

    # Test 1: Import the service
    print("\n1. Testing service import...")
    try:
        from app.services.google_forms_excel_service import GoogleFormsExcelService
        print("✅ Successfully imported GoogleFormsExcelService")

        # Create service instance with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            service = GoogleFormsExcelService(upload_folder=temp_dir)
            print(f"✅ Service instance created with temp folder: {temp_dir}")

        print("✅ Service initialization successful")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Service creation failed: {e}")
        return False

    # Test 2: Test filename generation
    print("\n2. Testing filename generation...")
    try:
        service = GoogleFormsExcelService()

        filename1 = service.generate_timestamp_filename("test", "Sample Form")
        filename2 = service.generate_timestamp_filename("export")

        print(f"Generated filename 1: {filename1}")
        print(f"Generated filename 2: {filename2}")

        # Check format
        if filename1.endswith('.xlsx') and 'Sample_Form' in filename1:
            print("✅ Filename generation working correctly")
        else:
            print("❌ Filename format incorrect")

    except Exception as e:
        print(f"❌ Filename generation failed: {e}")
        return False

    # Test 3: Test directory creation
    print("\n3. Testing directory management...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_upload_dir = os.path.join(temp_dir, 'test_exports')
            service = GoogleFormsExcelService(upload_folder=test_upload_dir)

            if os.path.exists(test_upload_dir):
                print("✅ Upload directory created successfully")
            else:
                print("❌ Upload directory not created")
                return False

    except Exception as e:
        print(f"❌ Directory management failed: {e}")
        return False

    # Test 4: Test Excel generation with mock data
    print("\n4. Testing Excel generation with mock data...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = GoogleFormsExcelService(upload_folder=temp_dir)

            # Create mock data
            mock_data = create_mock_google_forms_data()

            # Test the internal sheet creation methods
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Test Responses"

            # Test response export
            service._export_responses_to_sheet(
                ws,
                mock_data['responses'],
                mock_data['form_info']
            )

            # Check if data was written
            if ws.max_row > 1:  # Should have header + data rows
                print(f"✅ Responses exported to sheet ({ws.max_row} rows)")
            else:
                print("❌ No data written to responses sheet")
                return False

            # Test analytics sheet
            analytics_ws = wb.create_sheet("Analytics")
            service._export_analytics_to_sheet(
                analytics_ws,
                mock_data['analysis'],
                mock_data['form_info']
            )

            if analytics_ws.max_row > 1:
                print(f"✅ Analytics exported to sheet ({analytics_ws.max_row} rows)")
            else:
                print("❌ No data written to analytics sheet")
                return False

            # Test form info sheet
            info_ws = wb.create_sheet("Form Info")
            service._export_form_info_to_sheet(
                info_ws,
                mock_data['form_info'],
                mock_data
            )

            if info_ws.max_row > 1:
                print(f"✅ Form info exported to sheet ({info_ws.max_row} rows)")
            else:
                print("❌ No data written to form info sheet")
                return False

            # Save the workbook to test file creation
            test_file = os.path.join(temp_dir, "test_export.xlsx")
            wb.save(test_file)

            if os.path.exists(test_file):
                file_size = os.path.getsize(test_file)
                print(f"✅ Excel file created successfully ({file_size} bytes)")
            else:
                print("❌ Excel file not created")
                return False

    except Exception as e:
        print(f"❌ Excel generation failed: {e}")
        print(f"Error details: {str(e)}")
        return False

    # Test 5: Test data quality calculation
    print("\n5. Testing data quality calculation...")
    try:
        service = GoogleFormsExcelService()
        mock_data = create_mock_google_forms_data()

        quality_score = service._calculate_data_quality_score(mock_data['responses'])
        print(f"Data quality score: {quality_score:.2f}")

        if 0.0 <= quality_score <= 1.0:
            print("✅ Data quality calculation working")
        else:
            print("❌ Data quality score out of range")
            return False

    except Exception as e:
        print(f"❌ Data quality calculation failed: {e}")
        return False

    # Test 6: Check dependencies
    print("\n6. Testing required dependencies...")
    dependencies = [
        ('openpyxl', 'Excel file creation'),
        ('pandas', 'Data manipulation'),
        ('pathlib', 'Path handling'),
        ('uuid', 'Unique filename generation'),
        ('json', 'JSON handling'),
        ('datetime', 'Date/time processing')
    ]

    missing_deps = []
    for dep, purpose in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} available ({purpose})")
        except ImportError:
            print(f"❌ {dep} missing ({purpose})")
            missing_deps.append(dep)

    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)

    print("\nGoogle Forms Excel Export Service is ready!")
    print("\nTo use in production:")
    print("1. Configure Google OAuth credentials")
    print("2. Set up proper authentication")
    print("3. Test with real Google Forms API")
    print("4. Configure proper upload directories")
    print("5. Add error handling for production scenarios")

    return True

if __name__ == "__main__":
    success = test_google_forms_excel_service()
    if success:
        print("\n🎉 Google Forms Excel export functionality is working!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)