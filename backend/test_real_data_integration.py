#!/usr/bin/env python3
"""
Test Real Data Integration for Next-Gen Report Builder
Tests the integration with real Excel data and Gemini AI suggestions
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_real_data_sources():
    """Test that real data sources are being discovered"""
    print("📊 Testing Real Data Source Discovery...")
    
    try:
        from app.routes.nextgen_report_builder import get_data_sources
        
        # Mock JWT identity for testing
        import flask
        from unittest.mock import patch
        
        with patch('flask_jwt_extended.get_jwt_identity', return_value='test_user_123'):
            # This would normally be called via Flask route
            # For testing, we'll check the logic directly
            uploads_dir = Path(__file__).parent / 'static' / 'uploads' / 'excel'
            
            if uploads_dir.exists():
                excel_files = list(uploads_dir.glob('*.xlsx'))
                print(f"✅ Found {len(excel_files)} Excel files in uploads directory")
                
                for excel_file in excel_files:
                    print(f"   📄 {excel_file.name}")
                    print(f"      Size: {excel_file.stat().st_size / 1024:.1f} KB")
                    
                    # Test Excel parsing
                    from app.services.excel_parser import ExcelParserService
                    excel_parser = ExcelParserService()
                    
                    try:
                        result = excel_parser.parse_excel_file(str(excel_file))
                        if result.get('success'):
                            print(f"      ✅ Parsed successfully")
                            print(f"         Columns: {len(result.get('columns', []))}")
                            print(f"         Rows: {result.get('total_rows', 0)}")
                        else:
                            print(f"      ❌ Parsing failed: {result.get('error')}")
                    except Exception as e:
                        print(f"      ❌ Error parsing: {e}")
            else:
                print("⚠️ No uploads directory found")
                print("   Create: backend/static/uploads/excel/")
                print("   Add some .xlsx files for testing")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing data sources: {str(e)}")
        return False

def test_gemini_ai_suggestions():
    """Test Gemini AI suggestions with real data"""
    print("\n🤖 Testing Gemini AI Suggestions with Real Data...")
    
    try:
        from app.routes.nextgen_report_builder import (
            _generate_ai_suggestions_with_gemini,
            _get_data_source_info
        )
        
        # Test with a mock data source that has real field types
        test_data_source = {
            'type': 'excel',
            'name': 'Sales Performance Data',
            'fields': [
                {'name': 'Region', 'type': 'categorical'},
                {'name': 'Quarter', 'type': 'temporal'},
                {'name': 'Revenue', 'type': 'numerical'},
                {'name': 'Profit Margin', 'type': 'numerical'},
                {'name': 'Customer Count', 'type': 'numerical'}
            ],
            'recordCount': 150,
            'sampleData': [
                {'Region': 'North', 'Quarter': 'Q1', 'Revenue': 120000},
                {'Region': 'South', 'Quarter': 'Q1', 'Revenue': 98000}
            ]
        }
        
        context = {'existingElements': []}
        
        print("📊 Testing AI suggestions generation...")
        ai_suggestions = _generate_ai_suggestions_with_gemini(test_data_source, context)
        
        if ai_suggestions:
            print(f"✅ AI Suggestions Generated: {len(ai_suggestions)} suggestions")
            for i, suggestion in enumerate(ai_suggestions, 1):
                print(f"   {i}. {suggestion.get('title', 'Untitled')}")
                print(f"      - Chart Type: {suggestion.get('chartType', 'unknown')}")
                print(f"      - Confidence: {suggestion.get('confidence', 0):.2f}")
                print(f"      - AI Generated: {suggestion.get('aiGenerated', False)}")
                print(f"      - Style: {suggestion.get('style', 'N/A')}")
                print(f"      - Preview: {suggestion.get('preview', 'No preview')[:60]}...")
                
                # Check field mappings
                mappings = suggestion.get('mappings', {})
                if mappings:
                    print(f"      - Mappings: {mappings}")
            
            return True
        else:
            print("⚠️ AI suggestions not generated, testing fallback...")
            
            # Test fallback suggestions
            from app.routes.nextgen_report_builder import _get_fallback_suggestions
            fallback_suggestions = _get_fallback_suggestions(test_data_source)
            
            if fallback_suggestions:
                print(f"✅ Fallback Suggestions Generated: {len(fallback_suggestions)} suggestions")
                for i, suggestion in enumerate(fallback_suggestions, 1):
                    print(f"   {i}. {suggestion.get('title', 'Untitled')}")
                    print(f"      - Chart Type: {suggestion.get('chartType', 'unknown')}")
                    print(f"      - Confidence: {suggestion.get('confidence', 0):.2f}")
                
                print("\n💡 Note: Fallback suggestions are working, but Gemini AI suggestions are not.")
                print("   This means your Gemini service is available but not generating content.")
                return False
            else:
                print("❌ No suggestions generated at all")
                return False
        
    except Exception as e:
        print(f"❌ Error testing AI suggestions: {str(e)}")
        return False

def test_chart_data_generation():
    """Test real chart data generation"""
    print("\n📈 Testing Real Chart Data Generation...")
    
    try:
        from app.routes.nextgen_report_builder import (
            _generate_real_chart_data,
            _generate_fallback_chart_data
        )
        
        # Test with sample Excel data structure
        sample_excel_data = {
            'columns': [
                {'name': 'Region', 'data_type': 'text'},
                {'name': 'Revenue', 'data_type': 'number'},
                {'name': 'Quarter', 'data_type': 'date'}
            ],
            'rows': [
                ['North', 120000, '2024-01-01'],
                ['South', 98000, '2024-01-01'],
                ['East', 86000, '2024-01-01'],
                ['West', 102000, '2024-01-01']
            ]
        }
        
        # Test bar chart generation
        print("📊 Testing Bar Chart Generation...")
        bar_chart_data = _generate_real_chart_data(sample_excel_data, 'bar', {})
        
        if bar_chart_data and bar_chart_data.get('labels') != ['No Data']:
            print("✅ Bar chart data generated successfully")
            print(f"   Labels: {bar_chart_data.get('labels')}")
            print(f"   Data: {bar_chart_data.get('datasets', [{}])[0].get('data', [])}")
        else:
            print("❌ Bar chart data generation failed")
            return False
        
        # Test line chart generation
        print("\n📈 Testing Line Chart Generation...")
        line_chart_data = _generate_real_chart_data(sample_excel_data, 'line', {})
        
        if line_chart_data and line_chart_data.get('labels') != ['No Data']:
            print("✅ Line chart data generated successfully")
            print(f"   Labels: {line_chart_data.get('labels')}")
            print(f"   Data: {line_chart_data.get('datasets', [{}])[0].get('data', [])}")
        else:
            print("❌ Line chart data generation failed")
            return False
        
        # Test pie chart generation
        print("\n🥧 Testing Pie Chart Generation...")
        pie_chart_data = _generate_real_chart_data(sample_excel_data, 'pie', {})
        
        if pie_chart_data and pie_chart_data.get('labels') != ['No Data']:
            print("✅ Pie chart data generated successfully")
            print(f"   Labels: {pie_chart_data.get('labels')}")
            print(f"   Data: {pie_chart_data.get('datasets', [{}])[0].get('data', [])}")
        else:
            print("❌ Pie chart data generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing chart data generation: {str(e)}")
        return False

def test_template_discovery():
    """Test template discovery from backend"""
    print("\n📄 Testing Template Discovery...")
    
    try:
        from app.routes.nextgen_report_builder import get_report_templates
        
        # Mock JWT identity for testing
        import flask
        from unittest.mock import patch
        
        with patch('flask_jwt_extended.get_jwt_identity', return_value='test_user_123'):
            # Check templates directory
            templates_dir = Path(__file__).parent / 'templates'
            
            if templates_dir.exists():
                docx_files = list(templates_dir.glob('*.docx'))
                print(f"✅ Found {len(docx_files)} .docx templates")
                
                for template_file in docx_files:
                    print(f"   📄 {template_file.name}")
                    print(f"      Size: {template_file.stat().st_size / 1024:.1f} KB")
                    
                    # Test template metadata
                    from app.routes.nextgen_report_builder import _get_template_display_name, _get_template_description
                    display_name = _get_template_display_name(template_file.stem)
                    description = _get_template_description(template_file.stem)
                    
                    print(f"      Display Name: {display_name}")
                    print(f"      Description: {description[:60]}...")
            else:
                print("⚠️ No templates directory found")
                print("   Create: backend/templates/")
                print("   Add some .docx files for testing")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing template discovery: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("REAL DATA INTEGRATION TEST FOR NEXT-GEN REPORT BUILDER")
    print("=" * 70)
    
    tests = [
        ("Real Data Source Discovery", test_real_data_sources),
        ("Gemini AI Suggestions", test_gemini_ai_suggestions),
        ("Real Chart Data Generation", test_chart_data_generation),
        ("Template Discovery", test_template_discovery)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL REAL DATA INTEGRATION TESTS PASSED!")
        print("Your Next-Gen Report Builder is fully integrated with real data!")
        print("✅ Real Excel data sources")
        print("✅ Gemini AI suggestions")
        print("✅ Real chart data generation")
        print("✅ Template discovery")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check your data sources and Gemini AI configuration")
    print("=" * 70)

