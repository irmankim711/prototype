#!/usr/bin/env python3
"""
Test script to verify Excel parsing fix
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def test_excel_parsing_fix():
    """Test the fixed Excel parsing functionality"""
    print("🧪 Testing Excel parsing fix...")
    
    try:
        from app.services.excel_parser import ExcelParserService
        
        # Initialize the service
        excel_parser = ExcelParserService()
        
        # Create a simple test Excel file to verify parsing
        test_data = [
            ['Name', 'Age', 'City', 'Salary'],
            ['John Doe', 30, 'New York', 50000],
            ['Jane Smith', 25, 'Los Angeles', 45000],
            ['Bob Johnson', 35, 'Chicago', 60000],
            ['Alice Brown', 28, 'Houston', 52000]
        ]
        
        # Create test file using openpyxl
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            
            for row in test_data:
                ws.append(row)
            
            # Save test file
            test_file_path = backend_path / 'static' / 'uploads' / 'excel' / 'test_data.xlsx'
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            wb.save(str(test_file_path))
            
            print(f"✅ Created test Excel file: {test_file_path}")
            
            # Test parsing
            result = excel_parser.parse_excel_file(str(test_file_path))
            
            if result.get('success'):
                print(f"✅ Excel parsing successful!")
                print(f"📊 Tables found: {result.get('tables_count', 0)}")
                print(f"📈 Total rows: {result.get('total_rows', 0)}")
                print(f"📋 Total columns: {result.get('total_columns', 0)}")
                
                tables = result.get('tables', [])
                if tables:
                    table = tables[0]
                    print(f"\n🔍 Table details:")
                    print(f"  Name: {table.get('name', 'Unknown')}")
                    print(f"  Sheet: {table.get('sheet_name', 'Unknown')}")
                    print(f"  Rows: {table.get('row_count', 0)}")
                    print(f"  Columns: {table.get('column_count', 0)}")
                    print(f"  Headers: {table.get('headers', [])}")
                    
                    # Test column extraction
                    sys.path.insert(0, str(backend_path / 'app' / 'routes'))
                    
                    try:
                        from nextgen_report_builder import _extract_columns_from_tables, _convert_excel_columns_to_fields
                        
                        columns = _extract_columns_from_tables(tables)
                        print(f"\n✅ Extracted {len(columns)} columns:")
                        
                        for i, col in enumerate(columns):
                            print(f"  {i+1}. {col.get('name', 'Unknown')} ({col.get('data_type', 'unknown')})")
                            sample_values = col.get('sample_values', [])
                            if sample_values:
                                print(f"     Sample values: {sample_values[:3]}...")
                        
                        fields = _convert_excel_columns_to_fields(columns)
                        print(f"\n✅ Converted to {len(fields)} fields:")
                        
                        for i, field in enumerate(fields):
                            print(f"  {i+1}. {field.get('name', 'Unknown')} - {field.get('type', 'unknown')} ({field.get('dataType', 'unknown')})")
                        
                        # Clean up test file
                        test_file_path.unlink()
                        print(f"\n🧹 Cleaned up test file")
                        
                    except ImportError as e:
                        print(f"⚠️ Could not import column extraction functions: {e}")
                        print("This is expected if the backend isn't fully set up")
                
            else:
                print(f"❌ Excel parsing failed: {result.get('error')}")
                
        except ImportError:
            print("⚠️ openpyxl not available, skipping Excel file creation test")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔍 Excel Parsing Fix Test")
    print("=" * 50)
    
    test_excel_parsing_fix()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("1. The Excel parser should now work with a simpler table detection algorithm")
    print("2. Column extraction should properly identify all columns")
    print("3. Field conversion should create proper field definitions")
    print("\n💡 Now try uploading your Excel file 'SENARAI SEMAK PUNCAK ALAM.xlsx':")
    print("   - It should now show the correct number of fields and records")
    print("   - The data source should be properly configured")
