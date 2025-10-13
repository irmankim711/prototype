#!/usr/bin/env python3
"""
Test script to test if the template processing fix works
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_template_processing():
    """Test if the template processing fix works"""
    try:
        print("🔍 Testing template processing fix...")
        
        from app.services.template_optimizer import TemplateOptimizerService
        from app.services.excel_parser import ExcelParserService
        
        # Create services
        template_optimizer = TemplateOptimizerService()
        excel_parser = ExcelParserService()
        
        # Test Excel file path (use the one from the logs)
        excel_path = "backend/app/static/uploads/excel/1_88e4b38031a44db1bfc93f07a9ac593f_SENARAI SEMAK PUNCAK ALAM.xlsx"
        
        if not os.path.exists(excel_path):
            print(f"❌ Excel file not found: {excel_path}")
            return False
        
        print(f"✅ Excel file found: {excel_path}")
        
        # Parse Excel file
        print("📊 Parsing Excel file...")
        excel_data = excel_parser.parse_excel_file(excel_path)
        
        if not excel_data['success']:
            print(f"❌ Excel parsing failed: {excel_data['error']}")
            return False
        
        print(f"✅ Excel parsed successfully: {excel_data['tables_count']} tables, {excel_data['total_rows']} rows")
        
        # Test template path
        template_path = "backend/templates/Temp2.tex"
        
        if not os.path.exists(template_path):
            print(f"❌ Template file not found: {template_path}")
            return False
        
        print(f"✅ Template file found: {template_path}")
        
        # Read template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        print(f"✅ Template content loaded: {len(template_content)} characters")
        
        # Test template optimization
        print("🔧 Testing template optimization...")
        optimization_result = template_optimizer.optimize_template_with_excel(template_content, excel_path)
        
        if not optimization_result['success']:
            print(f"❌ Template optimization failed: {optimization_result['error']}")
            return False
        
        print("✅ Template optimization successful")
        
        # Check if program info was extracted
        context = optimization_result['context']
        program = context.get('program', {})
        
        print(f"📋 Program info extracted:")
        print(f"  - Title: {program.get('title', 'NOT FOUND')}")
        print(f"  - Date: {program.get('date', 'NOT FOUND')}")
        print(f"  - Objectives: {program.get('objectives', 'NOT FOUND')}")
        print(f"  - Location: {program.get('location', 'NOT FOUND')}")
        
        # Check if the critical 'objectives' field exists
        if 'objectives' in program:
            print("✅ Critical 'objectives' field found!")
            return True
        else:
            print("❌ Critical 'objectives' field missing!")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Template Processing Fix Test")
    print("=" * 50)
    
    success = test_template_processing()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Template processing fix test passed!")
        print("🎉 The 'objectives' field issue should be resolved!")
    else:
        print("❌ Template processing fix test failed!")
        print("🔧 More work needed to fix the template processing")
    print("🏁 Test completed")
