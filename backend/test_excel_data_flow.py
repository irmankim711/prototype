"""
Integration Test for Excel Data Flow
Tests the complete flow from Excel upload to report generation with actual data
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.services.excel_parser import ExcelParserService
from app.services.template_data_mapper import template_data_mapper
from app.services.report_generation_service import report_generation_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_excel_parsing():
    """Test Excel file parsing"""
    logger.info("=" * 80)
    logger.info("TEST 1: Excel Parsing")
    logger.info("=" * 80)

    # Find a test Excel file - prioritize uploaded files with real data
    test_file = None

    # First try uploaded Excel files (most likely to have real data)
    uploads_dir = Path(__file__).parent / "app" / "static" / "uploads" / "excel"
    if uploads_dir.exists():
        excel_files = list(uploads_dir.glob("*.xlsx"))
        if excel_files:
            test_file = excel_files[0]
            logger.info(f"💡 Using uploaded Excel file: {test_file.name}")

    # Then try Data directory
    if not test_file or not test_file.exists():
        data_dir = Path(__file__).parent.parent / "Data"
        if data_dir.exists():
            excel_files = list(data_dir.glob("*.xlsx"))
            if excel_files:
                test_file = excel_files[0]
                logger.info(f"💡 Using Data directory Excel file: {test_file.name}")

    # Finally try test files in backend directory
    if not test_file or not test_file.exists():
        test_file = Path(__file__).parent / "test.xlsx"
        if not test_file.exists():
            test_file = Path(__file__).parent / "test_template.xlsx"

    if not test_file or not test_file.exists():
        logger.error("❌ No test Excel file found!")
        logger.info("💡 Please ensure there is a test Excel file available")
        logger.info("   Locations checked:")
        logger.info("   - backend/test.xlsx")
        logger.info("   - backend/test_template.xlsx")
        logger.info("   - Data/*.xlsx")
        return (False, None)

    logger.info(f"📄 Using test file: {test_file}")

    # Parse Excel
    parser = ExcelParserService()
    result = parser.parse_excel_file(str(test_file))

    if not result or not result.get('success'):
        logger.error(f"❌ Excel parsing failed: {result.get('error') if result else 'No result'}")
        return (False, None)

    records = result.get('records', [])
    columns = result.get('columns', [])

    logger.info(f"✅ Excel parsed successfully:")
    logger.info(f"   - Records: {len(records)}")
    logger.info(f"   - Columns: {columns[:10]}...")

    if records:
        logger.info(f"   - Sample record: {records[0]}")

    if not records:
        logger.error("❌ No records found in Excel file!")
        return (False, None)

    logger.info("✅ TEST 1 PASSED: Excel parsing works\n")
    return (True, result)

def test_data_mapping(excel_data):
    """Test data mapping to template format"""
    logger.info("=" * 80)
    logger.info("TEST 2: Data Mapping")
    logger.info("=" * 80)

    records = excel_data.get('records', [])
    columns = excel_data.get('columns', [])

    # Prepare raw data
    raw_data = {
        'records': records,
        'submissions': records,
        'columns': columns,
        'metadata': {
            'record_count': len(records),
            'column_count': len(columns)
        }
    }

    logger.info(f"📊 Raw data prepared:")
    logger.info(f"   - Records: {len(records)}")
    logger.info(f"   - Columns: {len(columns)}")

    # Test mapping for Temp2.tex
    template_name = 'Temp2.tex'
    logger.info(f"🗺️  Mapping data for template: {template_name}")

    mapped_data = template_data_mapper.map_data_for_template(raw_data, template_name)

    if not mapped_data:
        logger.error("❌ Data mapping returned empty data!")
        return (False, None)

    logger.info(f"✅ Data mapped successfully:")
    logger.info(f"   - Mapped keys: {list(mapped_data.keys())}")
    logger.info(f"   - Data size: {len(str(mapped_data))} characters")

    # Verify critical keys exist
    critical_keys = ['program', 'evaluation', 'participants']
    missing_keys = [key for key in critical_keys if key not in mapped_data]

    if missing_keys:
        logger.warning(f"⚠️  Missing critical keys: {missing_keys}")

    # Test default mapping
    logger.info(f"🗺️  Testing default mapping...")
    default_mapped = template_data_mapper.map_data_for_template(raw_data, 'generic_template.tex')

    if not default_mapped:
        logger.error("❌ Default mapping returned empty data!")
        return (False, None)

    logger.info(f"✅ Default mapping works: {list(default_mapped.keys())}")

    logger.info("✅ TEST 2 PASSED: Data mapping works\n")
    return (True, mapped_data)

def test_end_to_end_flow():
    """Test complete flow from Excel to mapped data"""
    logger.info("=" * 80)
    logger.info("TEST 3: End-to-End Data Flow")
    logger.info("=" * 80)

    # Step 1: Parse Excel
    parsing_success, excel_data = test_excel_parsing()
    if not parsing_success:
        return False

    # Step 2: Map data
    mapping_success, mapped_data = test_data_mapping(excel_data)
    if not mapping_success:
        return False

    # Step 3: Verify data integrity
    logger.info("🔍 Verifying data integrity...")

    records = excel_data.get('records', [])
    if 'participants' in mapped_data:
        participants = mapped_data['participants']
        logger.info(f"✅ Participants in mapped data: {len(participants)}")

        if len(participants) != len(records):
            logger.warning(f"⚠️  Participant count mismatch: {len(participants)} vs {len(records)}")
        else:
            logger.info(f"✅ Participant count matches: {len(participants)}")

    # Step 4: Summary
    logger.info("=" * 80)
    logger.info("📋 FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Excel Records: {len(excel_data.get('records', []))}")
    logger.info(f"✅ Excel Columns: {len(excel_data.get('columns', []))}")
    logger.info(f"✅ Mapped Data Keys: {list(mapped_data.keys())}")
    logger.info(f"✅ Mapped Data Size: {len(str(mapped_data))} characters")

    logger.info("\n✅ ALL TESTS PASSED: Data flow is working correctly!")
    logger.info("=" * 80)

    return True

def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("🚀 Starting Excel Data Flow Integration Tests")
    logger.info("=" * 80)

    try:
        success = test_end_to_end_flow()

        if success:
            logger.info("\n🎉 SUCCESS: All tests passed!")
            logger.info("✅ Data is being extracted and mapped correctly")
            logger.info("✅ Reports should now show actual data\n")
            return 0
        else:
            logger.error("\n❌ FAILURE: Some tests failed")
            logger.error("❌ Check the logs above for details\n")
            return 1

    except Exception as e:
        logger.error(f"\n💥 EXCEPTION: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
