import sys
import os
import logging
import json

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.excel_data_extractor import ExcelDataExtractor
from app.services.enhanced_excel_parser import EnhancedExcelParser
from app.services.ai_enhanced_excel_service import AIEnhancedExcelService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_excel_config_loading():
    print("Testing Excel configuration loading...")
    
    # Test ExcelDataExtractor
    try:
        extractor = ExcelDataExtractor()
        if extractor.config:
            print("✅ ExcelDataExtractor loaded config successfully")
            # Verify specific config value
            if 'sheet_detection' in extractor.config:
                print("   - Found 'sheet_detection' in config")
            else:
                print("   ❌ 'sheet_detection' missing from config")
        else:
            print("❌ ExcelDataExtractor failed to load config")
    except Exception as e:
        print(f"❌ ExcelDataExtractor initialization failed: {e}")

    # Test EnhancedExcelParser
    try:
        parser = EnhancedExcelParser()
        if parser.config:
            print("✅ EnhancedExcelParser loaded config successfully")
             # Verify specific config value
            if 'field_categorization' in parser.config:
                print("   - Found 'field_categorization' in config")
            else:
                print("   ❌ 'field_categorization' missing from config")
        else:
            print("❌ EnhancedExcelParser failed to load config")
    except Exception as e:
        print(f"❌ EnhancedExcelParser initialization failed: {e}")

    # Test AIEnhancedExcelService
    try:
        service = AIEnhancedExcelService()
        if service.config:
            print("✅ AIEnhancedExcelService loaded config successfully")
             # Verify specific config value
            if 'type_detection' in service.config:
                print("   - Found 'type_detection' in config")
            else:
                print("   ❌ 'type_detection' missing from config")
        else:
            print("❌ AIEnhancedExcelService failed to load config")
    except Exception as e:
        print(f"❌ AIEnhancedExcelService initialization failed: {e}")

if __name__ == "__main__":
    test_excel_config_loading()
