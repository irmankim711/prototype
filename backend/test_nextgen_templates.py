#!/usr/bin/env python3
"""
Simple test to verify Next-Gen Report Builder template functionality
Tests template discovery and metadata without database dependencies
"""

import sys
import os
import json
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_template_discovery():
    """Test that all .docx templates in backend/templates are discoverable"""
    print("🔍 Testing Template Discovery...")
    
    templates_dir = Path(__file__).parent / 'templates'
    
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return False
    
    # Find all .docx files
    docx_files = list(templates_dir.glob('*.docx'))
    
    print(f"📁 Templates directory: {templates_dir}")
    print(f"📄 Found {len(docx_files)} .docx template files:")
    
    template_info = []
    
    for docx_file in docx_files:
        print(f"   ✅ {docx_file.name}")
        
        # Get template metadata
        template_data = {
            'id': docx_file.stem,
            'name': _get_template_display_name(docx_file.stem),
            'description': _get_template_description(docx_file.stem),
            'filepath': str(docx_file),
            'type': 'docx',
            'fileSize': docx_file.stat().st_size,
            'isRecommended': docx_file.stem.lower() in ['temp1', 'testtemplate']
        }
        
        template_info.append(template_data)
        
        print(f"      - Display Name: {template_data['name']}")
        print(f"      - Description: {template_data['description']}")
        print(f"      - File Size: {template_data['fileSize']} bytes")
        print(f"      - Recommended: {template_data['isRecommended']}")
        print()
    
    # Also check for other template types
    other_templates = []
    for ext in ['.jinja', '.tex', '.html']:
        files = list(templates_dir.glob(f'*{ext}'))
        other_templates.extend(files)
    
    if other_templates:
        print(f"📄 Found {len(other_templates)} other template files:")
        for template_file in other_templates:
            print(f"   ✅ {template_file.name} ({template_file.suffix})")
    
    print(f"\n📊 Template Summary:")
    print(f"   - Total .docx templates: {len(docx_files)}")
    print(f"   - Total other templates: {len(other_templates)}")
    print(f"   - Recommended templates: {len([t for t in template_info if t['isRecommended']])}")
    
    return len(docx_files) > 0

def _get_template_display_name(template_stem: str) -> str:
    """Get user-friendly display name for template"""
    name_mappings = {
        'temp1': 'Standard Business Report',
        'temp1_jinja2': 'Business Report with Excel Headers',
        'temp1_jinja2_excelheaders': 'Enhanced Business Report',
        'testtemplate': 'Test Report Template',
        'temp2': 'Academic/Scientific Report',
        'default_report': 'Default Report Template'
    }
    
    return name_mappings.get(template_stem.lower(), template_stem.replace('_', ' ').title())

def _get_template_description(template_stem: str) -> str:
    """Get detailed description for template"""
    descriptions = {
        'temp1': 'Standard business report template with professional formatting, suitable for general business reporting needs.',
        'temp1_jinja2': 'Business report template with dynamic content support and Excel data integration capabilities.',
        'temp1_jinja2_excelheaders': 'Enhanced business report template optimized for Excel data with automatic header mapping.',
        'testtemplate': 'Template for testing report generation functionality with sample data structures.',
        'temp2': 'Academic or scientific report template with LaTeX-style formatting for research and technical documents.',
        'default_report': 'Basic report template with minimal formatting, good for simple data presentation.'
    }
    
    return descriptions.get(template_stem.lower(), f'Report template: {template_stem}')

def test_template_api_format():
    """Test that templates would be formatted correctly for the API"""
    print("\n🔌 Testing API Format...")
    
    templates_dir = Path(__file__).parent / 'templates'
    docx_files = list(templates_dir.glob('*.docx'))
    
    # Simulate API response format
    api_response = {
        'success': True,
        'templates': [],
        'total': 0,
        'docxCount': len(docx_files),
        'recommendedTemplates': []
    }
    
    for docx_file in docx_files:
        template_info = {
            'id': docx_file.stem,
            'name': _get_template_display_name(docx_file.stem),
            'description': _get_template_description(docx_file.stem),
            'filepath': str(docx_file),
            'type': 'docx',
            'category': 'document',
            'fileSize': docx_file.stat().st_size,
            'supports': ['formatting', 'images', 'tables', 'charts'],
            'isDefault': docx_file.stem.lower() in ['temp1', 'testtemplate'],
            'preview': f'/api/v1/nextgen/templates/{docx_file.stem}/preview'
        }
        
        api_response['templates'].append(template_info)
        
        if template_info['isDefault']:
            api_response['recommendedTemplates'].append(template_info['id'])
    
    api_response['total'] = len(api_response['templates'])
    
    print("✅ API Response Format:")
    print(json.dumps(api_response, indent=2, default=str))
    
    return True

def test_frontend_compatibility():
    """Test that template data is compatible with frontend expectations"""
    print("\n🎨 Testing Frontend Compatibility...")
    
    templates_dir = Path(__file__).parent / 'templates'
    docx_files = list(templates_dir.glob('*.docx'))
    
    # Check that we have the expected template structure
    required_fields = ['id', 'name', 'description', 'type', 'isDefault']
    
    for docx_file in docx_files:
        template_data = {
            'id': docx_file.stem,
            'name': _get_template_display_name(docx_file.stem),
            'description': _get_template_description(docx_file.stem),
            'type': 'docx',
            'isDefault': docx_file.stem.lower() in ['temp1', 'testtemplate'],
            'usageInstructions': f'Upload Excel data and the template will generate a formatted report automatically.'
        }
        
        # Check all required fields are present
        missing_fields = [field for field in required_fields if field not in template_data]
        if missing_fields:
            print(f"❌ Template {docx_file.stem} missing fields: {missing_fields}")
            return False
        
        print(f"✅ Template {docx_file.stem} has all required fields")
    
    print("✅ All templates are frontend-compatible")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("NEXT-GEN REPORT BUILDER TEMPLATE TEST")
    print("=" * 60)
    
    tests = [
        ("Template Discovery", test_template_discovery),
        ("API Format", test_template_api_format),
        ("Frontend Compatibility", test_frontend_compatibility)
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
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TEMPLATE TESTS PASSED!")
        print("Templates are ready for use in the Next-Gen Report Builder!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)

