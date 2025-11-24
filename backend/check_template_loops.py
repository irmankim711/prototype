"""
Script to check if template has correct docxtpl loop syntax
"""
import sys
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def check_template_loops(template_path):
    """Check template for docxtpl loop syntax"""
    print("=" * 80)
    print(f"CHECKING TEMPLATE: {template_path.name}")
    print("=" * 80)

    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return

    print(f"✅ Template found")
    print(f"   Size: {template_path.stat().st_size} bytes")

    # DOCX files are ZIP archives
    with ZipFile(template_path, 'r') as zip_file:
        # Check document.xml which contains the main content
        with zip_file.open('word/document.xml') as doc_xml:
            content = doc_xml.read().decode('utf-8')

            # Look for docxtpl syntax
            print("\n" + "=" * 80)
            print("TEMPLATE SYNTAX CHECK")
            print("=" * 80)

            # Check for loop syntax
            if '{%tr for' in content:
                print("✅ Found {%tr for loop syntax (docxtpl table row loop)")
                # Extract the loop
                import re
                loops = re.findall(r'\{%tr\s+for\s+(\w+)\s+in\s+(\w+)\s*%\}', content)
                for item_var, list_var in loops:
                    print(f"   Loop: {item_var} in {list_var}")
            else:
                print("❌ No {%tr for loop syntax found")

            if '{%tr endfor' in content:
                print("✅ Found {%tr endfor (loop closing)")
            else:
                print("❌ No {%tr endfor found")

            if '{% for' in content and '{%tr for' not in content:
                print("⚠️ Found regular {% for loop (not {%tr) - this won't work for table rows!")
                loops = re.findall(r'\{%\s+for\s+(\w+)\s+in\s+(\w+)\s*%\}', content)
                for item_var, list_var in loops:
                    print(f"   Regular loop: {item_var} in {list_var}")

            # Check for peserta_list references
            print("\n" + "=" * 80)
            print("VARIABLE REFERENCES")
            print("=" * 80)

            if 'peserta_list' in content:
                print("✅ Found 'peserta_list' variable reference")
                # Count occurrences
                count = content.count('peserta_list')
                print(f"   Occurrences: {count}")
            else:
                print("❌ No 'peserta_list' variable found")

            # Check for placeholder syntax
            if '{{peserta.' in content:
                print("✅ Found {{peserta.field}} placeholders")
                # Extract field names
                import re
                fields = set(re.findall(r'\{\{peserta\.(\w+)\}\}', content))
                print(f"   Fields used: {', '.join(sorted(fields))}")
            else:
                print("❌ No {{peserta.field}} placeholders found")

            # Check for problematic syntax
            print("\n" + "=" * 80)
            print("SYNTAX WARNINGS")
            print("=" * 80)

            if '{{ ' in content or ' }}' in content:
                print("⚠️ Found spaces inside {{ }} - this may cause issues")

            if '{%' in content and ' for ' in content and 'peserta' not in content:
                print("⚠️ Found loop syntax but no 'peserta' variable")

            # Look for table structure
            if '<w:tbl>' in content:
                table_count = content.count('<w:tbl>')
                print(f"\n✅ Found {table_count} table(s) in template")

                # Check if loop is inside a table
                if '<w:tbl>' in content and '{%tr for' in content:
                    # Very basic check - see if loop is between table tags
                    table_start = content.find('<w:tbl>')
                    table_end = content.find('</w:tbl>')
                    loop_pos = content.find('{%tr for')

                    if table_start < loop_pos < table_end:
                        print("✅ Loop syntax is inside a table (correct placement)")
                    else:
                        print("⚠️ Loop syntax might not be inside a table")
            else:
                print("❌ No tables found in template")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    # Check both templates
    templates_dir = Path(__file__).parent / 'templates'

    templates = [
        templates_dir / 'report_template_copy.docx',
        templates_dir / 'UGS.docx'
    ]

    for template_path in templates:
        check_template_loops(template_path)
        print("\n")
