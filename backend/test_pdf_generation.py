"""
Test PDF Generation Functionality
Run this script to verify PDF export is working correctly
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def test_pdf_generation():
    """Test PDF generation with sample data"""
    print("Testing PDF generation...")
    
    try:
        from app.services.report_generator import create_pdf_report
        
        # Sample data for testing
        sample_data = {
            'form_name': 'Customer Feedback Form',
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_name': 'Test User',
            'entry_count': 15,
            'response_rate': 85.5,
            'title': 'Customer Feedback Analysis Report',
            'description': 'This report analyzes customer feedback collected through our feedback form.',
            'table_data': [
                ['Name', 'Email', 'Rating', 'Comments', 'Date'],
                ['John Doe', 'john@example.com', '5', 'Excellent service!', '2025-01-01'],
                ['Jane Smith', 'jane@example.com', '4', 'Good overall experience', '2025-01-02'],
                ['Bob Johnson', 'bob@example.com', '5', 'Very satisfied with the product', '2025-01-03'],
                ['Alice Brown', 'alice@example.com', '3', 'Average experience', '2025-01-04'],
                ['Charlie Wilson', 'charlie@example.com', '4', 'Would recommend to others', '2025-01-05']
            ],
            'statistics': {
                'Average Rating': 4.2,
                'Total Responses': 15,
                'Response Rate': '85.5%',
                'Most Common Rating': 5,
                'Completion Time (avg)': '3.5 minutes'
            },
            'ai_insights': [
                'Customer satisfaction is generally high with an average rating of 4.2/5',
                'Most customers (40%) gave the highest rating of 5 stars',
                'Response rate of 85.5% indicates good engagement',
                'Average completion time suggests the form is appropriately sized',
                'Comments indicate strong satisfaction with service quality'
            ]
        }
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        # Generate PDF
        result_path = create_pdf_report('form_analysis', sample_data, pdf_path)
        
        # Verify file was created
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"✅ PDF generated successfully!")
            print(f"   File: {result_path}")
            print(f"   Size: {file_size} bytes")
            
            # Clean up
            os.remove(result_path)
            print("✅ Test completed successfully!")
            return True
        else:
            print("❌ PDF file was not created")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please install ReportLab: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ Error during PDF generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generic_pdf():
    """Test generic PDF template"""
    print("\nTesting generic PDF template...")
    
    try:
        from app.services.report_generator import create_pdf_report
        
        generic_data = {
            'title': 'Monthly Sales Report',
            'description': 'Sales performance analysis for the current month.',
            'content': {
                'Executive Summary': 'Sales increased by 15% compared to last month.',
                'Key Metrics': [
                    'Total Revenue: $125,000',
                    'New Customers: 45',
                    'Conversion Rate: 3.2%',
                    'Average Order Value: $85'
                ],
                'Recommendations': [
                    'Increase marketing budget for high-performing channels',
                    'Focus on customer retention strategies',
                    'Expand product line based on customer feedback'
                ]
            },
            'table_data': [
                ['Product', 'Units Sold', 'Revenue', 'Growth'],
                ['Product A', '150', '$12,500', '+20%'],
                ['Product B', '200', '$18,000', '+15%'],
                ['Product C', '100', '$8,500', '+5%']
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        result_path = create_pdf_report('generic', generic_data, pdf_path)
        
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"✅ Generic PDF generated successfully!")
            print(f"   File: {result_path}")
            print(f"   Size: {file_size} bytes")
            
            os.remove(result_path)
            return True
        else:
            print("❌ Generic PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error during generic PDF generation: {e}")
        return False


def test_data_formatting():
    """Test the data formatting function"""
    print("\nTesting data formatting function...")
    
    try:
        from app.services.report_generator import format_report_data_for_pdf
        
        # Mock report object
        class MockReport:
            def __init__(self):
                self.id = 123
                self.title = "Test Report"
                self.status = "completed"
                self.created_at = datetime.now()
                self.data = {
                    'submissions': [
                        {'name': 'John', 'email': 'john@test.com', 'rating': 5},
                        {'name': 'Jane', 'email': 'jane@test.com', 'rating': 4}
                    ]
                }
        
        mock_report = MockReport()
        table_data = format_report_data_for_pdf(mock_report)
        
        if table_data and len(table_data) > 0:
            print("✅ Data formatting successful!")
            print(f"   Headers: {table_data[0]}")
            print(f"   Data rows: {len(table_data) - 1}")
            for i, row in enumerate(table_data[1:3], 1):  # Show first 2 data rows
                print(f"   Row {i}: {row}")
            return True
        else:
            print("❌ Data formatting failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error during data formatting: {e}")
        return False


if __name__ == "__main__":
    print("🔍 PDF Generation Test Suite")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # Run tests
    if test_pdf_generation():
        success_count += 1
    
    if test_generic_pdf():
        success_count += 1
    
    if test_data_formatting():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! PDF export functionality is ready.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    print("\nNext steps:")
    print("1. Install ReportLab if not already installed: pip install reportlab")
    print("2. Test the API endpoint: GET /api/reports/export/pdf/<report_id>")
    print("3. Integrate with frontend for download functionality")
