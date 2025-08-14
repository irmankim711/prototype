#!/usr/bin/env python3
"""
Test script to verify the template conversion fixes the 'p' undefined error
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.template_converter import TemplateConverter

def test_mustache_conversion():
    """Test Mustache to Jinja2 conversion with participant loop"""
    
    # Sample template content with participant loop
    mustache_template = """
{{#participants}}
{{participant.bil}} & {{participant.name}} & {{participant.pre_mark}} & {{participant.post_mark}} \\
{{/participants}}
"""
    
    print("🔍 Testing Mustache to Jinja2 conversion...")
    print("Original template:")
    print(mustache_template)
    
    # Convert template
    converted = TemplateConverter.mustache_to_jinja2(mustache_template)
    
    print("\nConverted template:")
    print(converted)
    
    # Test with sample context
    from jinja2 import Environment, Undefined
    env = Environment(undefined=Undefined)
    
    context = {
        'participants': [
            {'bil': '1', 'name': 'John Doe', 'pre_mark': '80', 'post_mark': '90'},
            {'bil': '2', 'name': 'Jane Smith', 'pre_mark': '75', 'post_mark': '85'}
        ]
    }
    
    try:
        template = env.from_string(converted)
        result = template.render(context)
        print("\n✅ Rendering successful!")
        print("Result:")
        print(result)
        return True
    except Exception as e:
        print(f"\n❌ Rendering failed: {e}")
        return False

def test_syntax_analysis():
    """Test template syntax analysis"""
    
    # Test different template types
    templates = {
        'mustache': '{{#participants}}{{participant.name}}{{/participants}}',
        'jinja2': '{% for p in participants %}{{ p.name }}{% endfor %}',
        'mixed': '{{#participants}}{{ p.name }}{{/participants}}{% if condition %}{% endif %}',
        'simple': '{{ program.title }} - {{ program.date }}'
    }
    
    print("\n🔍 Testing syntax analysis...")
    
    for expected_type, template_content in templates.items():
        detected_type = TemplateConverter.analyze_template_syntax(template_content)
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} {template_content[:30]}... -> {detected_type} (expected: {expected_type})")

if __name__ == "__main__":
    print("🧪 Template Converter Test Suite")
    print("=" * 50)
    
    success = test_mustache_conversion()
    test_syntax_analysis()
    
    if success:
        print("\n🎉 All tests passed! Template conversion should fix the 'p' undefined error.")
    else:
        print("\n💥 Tests failed. Template conversion needs more work.")
