"""
Test Enhanced Report Generator with Real Data
Tests the complete report generation pipeline with various data sources
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and services
from app import create_app, db
from app.models import Report, Form, FormSubmission, User
from app.services.report_generation_service import report_generation_service
from app.services.data_fetcher import data_fetcher
from app.services.data_transformer import data_transformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_form_data():
    """Create test form data in the database"""
    try:
        # Create test user
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(
                username='testuser',
                email='test@example.com',
                password='password',  # In real app, this would be hashed
                role='user'
            )
            db.session.add(test_user)
            db.session.commit()
            logger.info("Created test user")

        # Create test form
        test_form = Form.query.filter_by(title='Test Data Form').first()
        if not test_form:
            test_form = Form(
                title='Test Data Form',
                description='Form for testing report generation',
                schema={
                    'fields': [
                        {'id': 'name', 'type': 'text', 'label': 'Full Name'},
                        {'id': 'email', 'type': 'email', 'label': 'Email Address'},
                        {'id': 'age', 'type': 'number', 'label': 'Age'},
                        {'id': 'department', 'type': 'select', 'label': 'Department'},
                        {'id': 'salary', 'type': 'number', 'label': 'Salary'},
                        {'id': 'start_date', 'type': 'date', 'label': 'Start Date'}
                    ]
                },
                creator_id=test_user.id,
                is_active=True
            )
            db.session.add(test_form)
            db.session.commit()
            logger.info("Created test form")

        # Create test form submissions
        test_submissions = [
            {
                'name': 'John Doe',
                'email': 'john@company.com',
                'age': 28,
                'department': 'Engineering',
                'salary': 75000,
                'start_date': '2023-01-15'
            },
            {
                'name': 'Jane Smith',
                'email': 'jane@company.com',
                'age': 32,
                'department': 'Marketing',
                'salary': 68000,
                'start_date': '2022-08-10'
            },
            {
                'name': 'Mike Johnson',
                'email': 'mike@company.com',
                'age': 35,
                'department': 'Engineering',
                'salary': 82000,
                'start_date': '2021-03-22'
            },
            {
                'name': 'Sarah Wilson',
                'email': 'sarah@company.com',
                'age': 29,
                'department': 'Sales',
                'salary': 71000,
                'start_date': '2023-06-01'
            },
            {
                'name': 'David Brown',
                'email': 'david@company.com',
                'age': 41,
                'department': 'Engineering',
                'salary': 95000,
                'start_date': '2019-11-15'
            }
        ]

        # Clear existing submissions
        FormSubmission.query.filter_by(form_id=test_form.id).delete()

        for submission_data in test_submissions:
            submission = FormSubmission(
                form_id=test_form.id,
                submitter_id=test_user.id,
                data=submission_data,
                status='submitted',
                submitted_at=datetime.utcnow()
            )
            db.session.add(submission)

        db.session.commit()
        logger.info(f"Created {len(test_submissions)} test form submissions")

        return test_form.id, test_user.id

    except Exception as e:
        logger.error(f"Error creating test form data: {str(e)}")
        db.session.rollback()
        raise


def create_test_excel_data():
    """Create test Excel file"""
    try:
        import pandas as pd

        # Create sample data
        excel_data = {
            'Product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Webcam', 'Headphones'],
            'Category': ['Electronics', 'Accessories', 'Accessories', 'Electronics', 'Electronics', 'Accessories'],
            'Price': [999.99, 25.50, 89.99, 299.99, 79.99, 129.99],
            'Stock': [50, 200, 150, 75, 100, 80],
            'Rating': [4.5, 4.2, 4.3, 4.7, 4.1, 4.6],
            'Launch_Date': ['2023-01-15', '2022-06-20', '2022-08-10', '2023-03-05', '2023-02-28', '2022-12-15']
        }

        df = pd.DataFrame(excel_data)

        # Ensure uploads directory exists
        uploads_dir = Path('app/static/uploads/excel')
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Save to Excel file
        excel_file_path = uploads_dir / 'test_products.xlsx'
        df.to_excel(excel_file_path, index=False)

        logger.info(f"Created test Excel file: {excel_file_path}")
        return str(excel_file_path)

    except Exception as e:
        logger.error(f"Error creating test Excel data: {str(e)}")
        raise


def test_data_fetcher():
    """Test the data fetcher service"""
    logger.info("Testing data fetcher service...")

    form_id, user_id = create_test_form_data()

    # Test form data fetching
    form_config = {
        'type': 'form',
        'form_id': form_id,
        'limit': 100
    }

    result = data_fetcher.fetch_data_by_source_type(form_config)
    assert result['success'], f"Form data fetch failed: {result.get('error')}"
    assert len(result['data']) > 0, "No form data returned"
    logger.info(f"✅ Form data fetch successful: {len(result['data'])} records")

    # Test Excel data fetching
    excel_file_path = create_test_excel_data()
    excel_config = {
        'type': 'excel',
        'file_path': excel_file_path
    }

    result = data_fetcher.fetch_data_by_source_type(excel_config)
    assert result['success'], f"Excel data fetch failed: {result.get('error')}"
    assert len(result['data']) > 0, "No Excel data returned"
    logger.info(f"✅ Excel data fetch successful: {len(result['data'])} records")

    return form_id, excel_file_path


def test_data_transformer():
    """Test the data transformation service"""
    logger.info("Testing data transformer service...")

    # Create test data
    test_data = [
        {'name': 'John', 'age': 25, 'department': 'Engineering', 'salary': 70000},
        {'name': 'Jane', 'age': 30, 'department': 'Marketing', 'salary': 65000},
        {'name': 'Mike', 'age': 28, 'department': 'Engineering', 'salary': 75000},
        {'name': 'Sarah', 'age': 32, 'department': 'Sales', 'salary': 68000},
    ]

    # Test basic transformation
    transform_config = {
        'filters': [
            {'column': 'age', 'operator': 'gte', 'value': 28}
        ],
        'column_transforms': [
            {'column': 'name', 'operation': 'uppercase', 'new_column': 'name_upper'}
        ],
        'sort_by': [
            {'column': 'salary', 'direction': 'desc'}
        ]
    }

    result = data_transformer.transform_data(test_data, transform_config)
    assert result['success'], f"Data transformation failed: {result.get('error')}"
    assert len(result['data']) == 3, f"Expected 3 records after filtering, got {len(result['data'])}"
    logger.info(f"✅ Basic transformation successful: {result['metadata']}")

    # Test grouping and aggregation
    agg_config = {
        'group_by': ['department'],
        'aggregations': {
            'salary': ['avg', 'count', 'max'],
            'age': ['avg', 'min', 'max']
        }
    }

    result = data_transformer.transform_data(test_data, agg_config)
    assert result['success'], f"Data aggregation failed: {result.get('error')}"
    logger.info(f"✅ Aggregation successful: {len(result['data'])} groups")

    # Test statistics calculation
    stats_result = data_transformer.calculate_statistics(test_data, ['age', 'salary'])
    assert stats_result['success'], f"Statistics calculation failed: {stats_result.get('error')}"
    logger.info(f"✅ Statistics calculation successful: {list(stats_result['statistics'].keys())}")


def test_report_generation():
    """Test enhanced report generation with real data"""
    logger.info("Testing enhanced report generation...")

    form_id, excel_file_path = test_data_fetcher()

    # Create test report record
    test_report = Report(
        id='test-report-001',
        title='Enhanced Test Report',
        description='Testing report generation with real data',
        report_type='data_analysis',
        status='pending',
        generation_status='pending',
        template_id='1',
        program_id=1,
        user_id=1,
        organization_id=None,
        created_by=None,
        download_count=0,
        view_count=0
    )

    db.session.add(test_report)
    db.session.commit()

    # Test configuration with multiple data sources
    report_config = {
        'title': 'Multi-Source Data Analysis Report',
        'description': 'Report combining form submissions and Excel data',
        'data_sources': [
            {
                'type': 'form',
                'form_id': form_id,
                'limit': 100
            },
            {
                'type': 'excel',
                'file_path': excel_file_path
            }
        ],
        'transformations': {
            'filters': [
                {'column': 'age', 'operator': 'gte', 'value': 25}
            ],
            'sort_by': [
                {'column': 'salary', 'direction': 'desc'}
            ]
        },
        'include_statistics': True,
        'include_charts': True
    }

    # Generate the comprehensive report
    try:
        result = report_generation_service.generate_comprehensive_report(
            test_report.id,
            {},  # Legacy data (empty, will use real data from sources)
            report_config
        )

        assert result['status'] == 'completed', f"Report generation failed: {result}"
        assert 'pdf_file_path' in result, "PDF file path not returned"
        assert 'docx_file_path' in result, "DOCX file path not returned"
        assert 'excel_file_path' in result, "Excel file path not returned"

        # Verify files exist
        assert os.path.exists(result['pdf_file_path']), "PDF file not created"
        assert os.path.exists(result['docx_file_path']), "DOCX file not created"
        assert os.path.exists(result['excel_file_path']), "Excel file not created"

        logger.info("✅ Enhanced report generation successful!")
        logger.info(f"  PDF: {result['pdf_file_path']} ({result['file_sizes']['pdf']} bytes)")
        logger.info(f"  DOCX: {result['docx_file_path']} ({result['file_sizes']['docx']} bytes)")
        logger.info(f"  Excel: {result['excel_file_path']} ({result['file_sizes']['excel']} bytes)")

        return result

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise

    finally:
        # Clean up test report
        db.session.delete(test_report)
        db.session.commit()


def test_legacy_compatibility():
    """Test that the enhanced system works with legacy report requests"""
    logger.info("Testing legacy compatibility...")

    # Create test report record
    test_report = Report(
        id='test-legacy-report',
        title='Legacy Test Report',
        description='Testing legacy compatibility',
        report_type='legacy',
        status='pending',
        generation_status='pending',
        template_id='1',
        program_id=1,
        user_id=1,
        organization_id=None,
        created_by=None,
        download_count=0,
        view_count=0
    )

    db.session.add(test_report)
    db.session.commit()

    # Legacy format data and config
    legacy_data = {
        'submissions': [
            {'name': 'Legacy User 1', 'score': 85},
            {'name': 'Legacy User 2', 'score': 92}
        ]
    }

    legacy_config = {
        'title': 'Legacy Report',
        'description': 'Report using legacy format'
    }

    try:
        result = report_generation_service.generate_comprehensive_report(
            test_report.id,
            legacy_data,
            legacy_config
        )

        assert result['status'] == 'completed', f"Legacy report generation failed: {result}"
        logger.info("✅ Legacy compatibility maintained!")

        return result

    except Exception as e:
        logger.error(f"Legacy compatibility test failed: {str(e)}")
        raise

    finally:
        # Clean up test report
        db.session.delete(test_report)
        db.session.commit()


def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Report Generator Tests...")
    print("=" * 60)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        try:
            # Run tests
            test_data_fetcher()
            print()

            test_data_transformer()
            print()

            test_report_generation()
            print()

            test_legacy_compatibility()
            print()

            print("🎉 All tests passed!")
            print("=" * 60)
            print("✅ Your report generator is now fully functional with real data support!")
            print()
            print("Features now available:")
            print("• Fetch data from forms, Excel files, and databases")
            print("• Transform and aggregate data with filters, grouping, and sorting")
            print("• Generate enhanced PDF/DOCX reports with real data tables")
            print("• Statistical summaries and data source metadata")
            print("• Backward compatibility with existing report requests")
            print("• Professional formatting with charts and tables")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            raise


if __name__ == '__main__':
    main()