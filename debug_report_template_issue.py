#!/usr/bin/env python3
"""
Debug Script: Report Template Population Issue
Identifies why reports show only template without data
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_template_rendering():
    """Test template rendering with sample data"""
    try:
        from jinja2 import Template

        # Sample template content (similar to what might be in LaTeX)
        template_content = """
\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\title{{{ title }}}
\\author{{{ author }}}
\\date{{{ date }}}

\\begin{document}
\\maketitle

\\section{Summary}
Total records: {{ total_records }}

\\section{Data}
{% for record in records %}
\\subsection{Record {{ loop.index }}}
Name: {{ record.name }}
Email: {{ record.email }}
Status: {{ record.status }}
{% endfor %}

\\end{document}
"""

        # Sample data that should populate the template
        sample_data = {
            'title': 'Test Report',
            'author': 'Test Author',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_records': 3,
            'records': [
                {'name': 'John Doe', 'email': 'john@example.com', 'status': 'Active'},
                {'name': 'Jane Smith', 'email': 'jane@example.com', 'status': 'Inactive'},
                {'name': 'Bob Johnson', 'email': 'bob@example.com', 'status': 'Active'}
            ]
        }

        print("=" * 80)
        print("TESTING TEMPLATE RENDERING")
        print("=" * 80)

        # Test Jinja2 rendering
        template = Template(template_content)
        rendered_content = template.render(**sample_data)

        print("\n✅ Template rendering SUCCESSFUL")
        print("\nRendered Content:")
        print("-" * 40)
        print(rendered_content)
        print("-" * 40)

        return True, rendered_content

    except Exception as e:
        print(f"\n❌ Template rendering FAILED: {str(e)}")
        return False, str(e)

def test_data_fetching():
    """Test data fetching functionality"""
    try:
        print("\n" + "=" * 80)
        print("TESTING DATA FETCHING")
        print("=" * 80)

        # Import data fetcher
        from backend.app.services.data_fetcher import data_fetcher

        # Sample data source config
        sample_config = {
            'data_sources': [
                {
                    'type': 'form_submissions',
                    'source_id': 1,
                    'filters': {}
                }
            ]
        }

        # Test data fetching
        result = data_fetcher.fetch_data_by_source_type(sample_config['data_sources'][0])

        print(f"✅ Data fetching result: {result}")

        return True, result

    except Exception as e:
        print(f"\n❌ Data fetching FAILED: {str(e)}")
        logger.exception("Data fetching error")
        return False, str(e)

def test_report_generation_flow():
    """Test the full report generation flow"""
    try:
        print("\n" + "=" * 80)
        print("TESTING REPORT GENERATION FLOW")
        print("=" * 80)

        # Import necessary modules
        from backend.app.services.report_generation_service import report_generation_service

        # Test data that should be used in report
        test_data = {
            'records': [
                {'name': 'Test User 1', 'email': 'test1@example.com', 'date': '2024-01-01'},
                {'name': 'Test User 2', 'email': 'test2@example.com', 'date': '2024-01-02'}
            ],
            'metadata': {
                'sources': {
                    'source_1': {
                        'source_id': 'test_form',
                        'row_count': 2
                    }
                },
                'total_records': 2,
                'fetched_at': datetime.now().isoformat()
            },
            'summary': {
                'record_count': 2,
                'column_count': 3
            }
        }

        # Test configuration
        test_config = {
            'title': 'Debug Test Report',
            'base_url': 'http://localhost:5000',
            'include_excel': True
        }

        print(f"Test data keys: {list(test_data.keys())}")
        print(f"Records count: {len(test_data['records'])}")
        print(f"Sample record: {test_data['records'][0] if test_data['records'] else 'No records'}")

        # Test enhanced PDF generation
        pdf_path, pdf_size = report_generation_service.generate_enhanced_pdf_report(test_data, test_config)
        print(f"✅ PDF generated: {pdf_path} ({pdf_size} bytes)")

        # Test enhanced DOCX generation
        docx_path, docx_size = report_generation_service.generate_enhanced_docx_report(test_data, test_config)
        print(f"✅ DOCX generated: {docx_path} ({docx_size} bytes)")

        # Test Excel generation
        excel_path, excel_size = report_generation_service.generate_excel_report(test_data['records'], test_config)
        print(f"✅ Excel generated: {excel_path} ({excel_size} bytes)")

        return True, {
            'pdf_path': pdf_path,
            'docx_path': docx_path,
            'excel_path': excel_path
        }

    except Exception as e:
        print(f"\n❌ Report generation flow FAILED: {str(e)}")
        logger.exception("Report generation error")
        return False, str(e)

def check_latex_templates():
    """Check LaTeX templates for data binding issues"""
    try:
        print("\n" + "=" * 80)
        print("CHECKING LATEX TEMPLATES")
        print("=" * 80)

        # Check template directory
        template_dir = os.path.join('backend', 'templates')
        if not os.path.exists(template_dir):
            print(f"❌ Template directory not found: {template_dir}")
            return False, "Template directory missing"

        # List template files
        template_files = [f for f in os.listdir(template_dir) if f.endswith(('.tex', '.docx'))]
        print(f"Found {len(template_files)} template files:")
        for file in template_files:
            print(f"  - {file}")

        # Check specific template content
        for template_file in template_files:
            if template_file.endswith('.tex'):
                template_path = os.path.join(template_dir, template_file)
                print(f"\nChecking {template_file}:")

                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for Jinja2 variables
                import re
                jinja_vars = re.findall(r'\{\{\s*([^}]+)\s*\}\}', content)
                print(f"  Jinja2 variables found: {jinja_vars}")

                # Check for common data fields
                data_fields = ['title', 'author', 'date', 'records', 'data', 'submissions']
                found_fields = [field for field in data_fields if field in content]
                print(f"  Common data fields: {found_fields}")

                if not jinja_vars and not found_fields:
                    print(f"  ⚠️  WARNING: Template appears to be static (no variables)")
                else:
                    print(f"  ✅ Template has dynamic content")

        return True, template_files

    except Exception as e:
        print(f"\n❌ Template check FAILED: {str(e)}")
        return False, str(e)

def main():
    """Main debugging function"""
    print("🔍 DEBUGGING REPORT TEMPLATE POPULATION ISSUE")
    print("=" * 80)

    results = {}

    # Test 1: Template rendering
    success, result = test_template_rendering()
    results['template_rendering'] = {'success': success, 'result': result}

    # Test 2: Data fetching
    success, result = test_data_fetching()
    results['data_fetching'] = {'success': success, 'result': result}

    # Test 3: LaTeX templates
    success, result = check_latex_templates()
    results['latex_templates'] = {'success': success, 'result': result}

    # Test 4: Report generation flow
    success, result = test_report_generation_flow()
    results['report_generation'] = {'success': success, 'result': result}

    # Summary
    print("\n" + "=" * 80)
    print("DEBUGGING SUMMARY")
    print("=" * 80)

    for test_name, test_result in results.items():
        status = "✅ PASS" if test_result['success'] else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not test_result['success']:
            print(f"  Error: {test_result['result']}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if not results['template_rendering']['success']:
        print("1. Fix Jinja2 template syntax issues")

    if not results['data_fetching']['success']:
        print("2. Fix data fetching service configuration")

    if not results['latex_templates']['success']:
        print("3. Check LaTeX template files and directory structure")

    if not results['report_generation']['success']:
        print("4. Debug report generation service")
    else:
        print("✅ All tests passed - report generation should work correctly")
        print("   If you're still seeing template-only output, check:")
        print("   - Frontend report display logic")
        print("   - API response handling")
        print("   - File download mechanisms")

if __name__ == "__main__":
    main()