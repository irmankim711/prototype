#!/usr/bin/env python3
"""
Simple test to isolate the .content attribute error
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.services.template_converter import TemplateConverter

def test_converter():
    """Test the template converter"""
    
    # Sample LaTeX content with Mustache syntax
    sample_latex = """
    \\documentclass{article}
    \\begin{document}
    
    Title: {{title}}
    
    {{#participants}}
    Name: {{item.name}}
    {{/participants}}
    
    \\end{document}
    """
    
    try:
        print("Testing template syntax analysis...")
        syntax_type = TemplateConverter.analyze_template_syntax(sample_latex)
        print(f"Detected syntax: {syntax_type}")
        
        print("Testing Mustache to Jinja2 conversion...")
        converted = TemplateConverter.mustache_to_jinja2(sample_latex)
        print("Conversion successful!")
        print("Converted template:")
        print(converted)
        
        return True
        
    except Exception as e:
        print(f"Converter test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_converter()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
