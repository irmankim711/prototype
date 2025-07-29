#!/usr/bin/env python3
"""
Test LaTeX template processing in isolation
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.services.template_converter import TemplateConverter
from jinja2 import Template, DebugUndefined

def test_latex_processing():
    """Test the exact LaTeX processing logic from mvp.py"""
    
    # Read the actual Temp2.tex file
    template_path = os.path.join('templates', 'Temp2.tex')
    
    try:
        print(f"Reading template from: {template_path}")
        with open(template_path, 'r', encoding='utf-8') as f:
            latex_content = f.read()
        
        print(f"Template content length: {len(latex_content)}")
        
        # Test data - more complete
        context = {
            'title': 'Test Project',
            'general_description': 'This is a test description',
            'program': {
                'title': 'Sample Program',
                'date': '2025-01-20',
                'location': 'Test Location',
                'organizer': 'Test Organizer',
                'speaker': 'Test Speaker',
                'trainer': 'Test Trainer',
                'facilitator': 'Test Facilitator',
                'male_participants': '5',
                'female_participants': '7',
                'total_participants': '12',
                'background': 'Test Background',
                'objectives': 'Test Objectives'
            },
            'tentative': {
                'day1': [
                    {
                        'time': '9:00 AM',
                        'activity': 'Opening Ceremony',
                        'description': 'Welcome remarks',
                        'handler': 'John Doe'
                    }
                ],
                'day2': [
                    {
                        'time': '9:00 AM', 
                        'activity': 'Closing',
                        'description': 'Summary and closing',
                        'handler': 'Jane Smith'
                    }
                ]
            },
            'participants': [
                {
                    'name': 'Alice Johnson',
                    'organization': 'Company A',
                    'position': 'Manager'
                },
                {
                    'name': 'Bob Smith', 
                    'organization': 'Company B',
                    'position': 'Director'
                }
            ],
            'evaluation': {
                'content': {
                    'objective': {'1': '0', '2': '0', '3': '0', '4': '0', '5': '0'},
                    'impact': {'1': '0', '2': '0', '3': '0', '4': '0', '5': '0'},
                    'duration': {'1': '0', '2': '0', '3': '0', '4': '0', '5': '0'}
                },
                'tools': {
                    'notes': {'1': '0', '2': '0', '3': '0', '4': '0', '5': '0'},
                    'notes_clarity': {'1': '0', '2': '0', '3': '0', '4': '0', '5': '0'}
                }
            },
            'attendance': {'total_attended': '10', 'total_absent': '2'},
            'suggestions': {'consultant': [], 'participants': []},
            'signature': {
                'consultant': {'name': 'Consultant Name'},
                'executive': {'name': 'Executive Name'},
                'head': {'name': 'Head Name'}
            },
            'images': []
        }
        
        print(f"Context received: {list(context.keys())}")
        
        # Analyze and convert template syntax if needed
        syntax_type = TemplateConverter.analyze_template_syntax(latex_content)
        print(f"Detected template syntax: {syntax_type}")
        
        if syntax_type in ['mustache', 'mixed']:
            print("Converting Mustache syntax to Jinja2")
            latex_content = TemplateConverter.mustache_to_jinja2(latex_content)
            context = TemplateConverter.prepare_context_for_mustache_conversion(context)
        
        # Transform flat context data to nested structure
        nested_context = {}
        for key, value in context.items():
            if '.' in key:
                parts = key.split('.')
                current = nested_context
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                nested_context[key] = value
        
        print(f"Nested context created: {list(nested_context.keys())}")
        
        # Use Jinja2 to render LaTeX with nested data and loops
        print("Creating Jinja2 template...")
        template = Template(latex_content, undefined=DebugUndefined)
        
        print("Rendering template...")
        rendered_latex = template.render(nested_context)
        
        print(f"Template rendered successfully! Length: {len(rendered_latex)}")
        print("First 500 characters of rendered content:")
        print(rendered_latex[:500])
        
        return True
        
    except Exception as e:
        print(f"LaTeX processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_latex_processing()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
