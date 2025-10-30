"""
Test AI-Enhanced Excel Generation
"""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.ai_enhanced_excel_service import ai_excel_service


def test_basic_excel_generation():
    """Test basic Excel generation with sample data"""
    print("\n" + "="*60)
    print("TEST 1: Basic Excel Generation")
    print("="*60)

    # Sample sales data
    sample_data = [
        {
            "date": "2024-01-15",
            "product": "Laptop",
            "category": "Electronics",
            "quantity": 5,
            "unit_price": 999.99,
            "total": 4999.95,
            "region": "North"
        },
        {
            "date": "2024-01-16",
            "product": "Mouse",
            "category": "Electronics",
            "quantity": 20,
            "unit_price": 29.99,
            "total": 599.80,
            "region": "South"
        },
        {
            "date": "2024-01-17",
            "product": "Keyboard",
            "category": "Electronics",
            "quantity": 15,
            "unit_price": 79.99,
            "total": 1199.85,
            "region": "East"
        },
        {
            "date": "2024-01-18",
            "product": "Monitor",
            "category": "Electronics",
            "quantity": 8,
            "unit_price": 349.99,
            "total": 2799.92,
            "region": "West"
        },
        {
            "date": "2024-01-19",
            "product": "Webcam",
            "category": "Electronics",
            "quantity": 12,
            "unit_price": 89.99,
            "total": 1079.88,
            "region": "North"
        },
        {
            "date": "2024-01-20",
            "product": "Headset",
            "category": "Electronics",
            "quantity": 18,
            "unit_price": 59.99,
            "total": 1079.82,
            "region": "South"
        },
        {
            "date": "2024-01-21",
            "product": "USB Cable",
            "category": "Accessories",
            "quantity": 50,
            "unit_price": 9.99,
            "total": 499.50,
            "region": "East"
        },
        {
            "date": "2024-01-22",
            "product": "Mouse Pad",
            "category": "Accessories",
            "quantity": 30,
            "unit_price": 14.99,
            "total": 449.70,
            "region": "West"
        }
    ]

    try:
        # Generate Excel with AI enhancements
        file_path, file_size = ai_excel_service.generate_enhanced_excel(
            data=sample_data,
            title="Sales Report - January 2024",
            options={
                'include_charts': True,
                'include_summary': True,
                'include_pivot': False
            }
        )

        print(f"\n✅ Excel file generated successfully!")
        print(f"📄 File: {file_path}")
        print(f"📊 Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        print(f"📈 Records: {len(sample_data)}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_form_submissions_excel():
    """Test Excel generation with form submission data"""
    print("\n" + "="*60)
    print("TEST 2: Form Submissions Excel Generation")
    print("="*60)

    # Sample form submission data
    sample_data = [
        {
            "id": 1,
            "submitted_at": "2024-01-15T10:30:00",
            "status": "completed",
            "submitter_email": "john@example.com",
            "full_name": "John Doe",
            "age": 28,
            "department": "Engineering",
            "satisfaction_score": 9,
            "comments": "Great service!"
        },
        {
            "id": 2,
            "submitted_at": "2024-01-15T11:45:00",
            "status": "completed",
            "submitter_email": "jane@example.com",
            "full_name": "Jane Smith",
            "age": 32,
            "department": "Marketing",
            "satisfaction_score": 8,
            "comments": "Very satisfied"
        },
        {
            "id": 3,
            "submitted_at": "2024-01-15T14:20:00",
            "status": "completed",
            "submitter_email": "bob@example.com",
            "full_name": "Bob Johnson",
            "age": 45,
            "department": "Sales",
            "satisfaction_score": 10,
            "comments": "Excellent!"
        },
        {
            "id": 4,
            "submitted_at": "2024-01-16T09:15:00",
            "status": "completed",
            "submitter_email": "alice@example.com",
            "full_name": "Alice Williams",
            "age": 29,
            "department": "Engineering",
            "satisfaction_score": 7,
            "comments": "Good overall"
        },
        {
            "id": 5,
            "submitted_at": "2024-01-16T13:30:00",
            "status": "completed",
            "submitter_email": "charlie@example.com",
            "full_name": "Charlie Brown",
            "age": 38,
            "department": "HR",
            "satisfaction_score": 9,
            "comments": "Very helpful"
        }
    ]

    try:
        file_path, file_size = ai_excel_service.generate_enhanced_excel(
            data=sample_data,
            title="Customer Satisfaction Survey Results",
            options={
                'include_charts': True,
                'include_summary': True,
                'include_pivot': False
            }
        )

        print(f"\n✅ Excel file generated successfully!")
        print(f"📄 File: {file_path}")
        print(f"📊 Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        print(f"📈 Records: {len(sample_data)}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_data_excel():
    """Test Excel generation with financial data"""
    print("\n" + "="*60)
    print("TEST 3: Financial Data Excel Generation")
    print("="*60)

    # Sample financial data
    sample_data = [
        {
            "month": "January",
            "revenue": 125000.50,
            "expenses": 87500.25,
            "profit": 37500.25,
            "profit_margin": 0.30,
            "growth_rate": 0.15
        },
        {
            "month": "February",
            "revenue": 135000.75,
            "expenses": 92000.50,
            "profit": 43000.25,
            "profit_margin": 0.32,
            "growth_rate": 0.08
        },
        {
            "month": "March",
            "revenue": 145000.00,
            "expenses": 95000.75,
            "profit": 50000.25,
            "profit_margin": 0.34,
            "growth_rate": 0.07
        },
        {
            "month": "April",
            "revenue": 152000.25,
            "expenses": 98000.00,
            "profit": 54000.25,
            "profit_margin": 0.36,
            "growth_rate": 0.05
        },
        {
            "month": "May",
            "revenue": 160000.50,
            "expenses": 100000.25,
            "profit": 60000.25,
            "profit_margin": 0.38,
            "growth_rate": 0.05
        },
        {
            "month": "June",
            "revenue": 175000.75,
            "expenses": 105000.50,
            "profit": 70000.25,
            "profit_margin": 0.40,
            "growth_rate": 0.09
        }
    ]

    try:
        file_path, file_size = ai_excel_service.generate_enhanced_excel(
            data=sample_data,
            title="Financial Performance Report Q1-Q2 2024",
            options={
                'include_charts': True,
                'include_summary': True,
                'include_pivot': False
            }
        )

        print(f"\n✅ Excel file generated successfully!")
        print(f"📄 File: {file_path}")
        print(f"📊 Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        print(f"📈 Records: {len(sample_data)}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI-ENHANCED EXCEL GENERATION TEST SUITE")
    print("="*60)

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("\n⚠️  Warning: ANTHROPIC_API_KEY not found in environment")
        print("Please set your Anthropic API key to enable AI features")
        print("\nTests will run but AI analysis will be limited")

    results = []

    # Run tests
    results.append(("Basic Excel Generation", test_basic_excel_generation()))
    results.append(("Form Submissions Excel", test_form_submissions_excel()))
    results.append(("Financial Data Excel", test_financial_data_excel()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
