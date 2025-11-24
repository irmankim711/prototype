"""
Extract readable text from template to see the actual content
"""
import sys
from pathlib import Path
from zipfile import ZipFile
import re

sys.path.insert(0, str(Path(__file__).parent))

def extract_template_content(template_path):
    """Extract text content from DOCX"""
    print("=" * 80)
    print(f"EXTRACTING CONTENT FROM: {template_path.name}")
    print("=" * 80)

    with ZipFile(template_path, 'r') as zip_file:
        with zip_file.open('word/document.xml') as doc_xml:
            content = doc_xml.read().decode('utf-8')

            # Find all Jinja2/docxtpl syntax
            jinja_patterns = re.findall(r'\{[{%].*?[}%]\}', content)

            print(f"\nFound {len(jinja_patterns)} Jinja2/docxtpl patterns:\n")

            for i, pattern in enumerate(jinja_patterns, 1):
                print(f"{i}. {pattern}")

            # Look specifically for table-related loops
            print("\n" + "=" * 80)
            print("LOOKING FOR TABLE LOOP STRUCTURE")
            print("=" * 80)

            # Find the section with peserta_list
            peserta_sections = []
            for match in re.finditer(r'.{0,200}peserta.{0,200}', content):
                section = match.group(0)
                # Clean up XML tags for readability
                cleaned = re.sub(r'<[^>]+>', ' ', section)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                if cleaned and cleaned not in peserta_sections:
                    peserta_sections.append(cleaned)

            print("\nSections containing 'peserta':")
            for i, section in enumerate(peserta_sections[:10], 1):  # Show first 10
                print(f"\n{i}. {section[:200]}...")

if __name__ == '__main__':
    templates_dir = Path(__file__).parent / 'templates'

    # Check UGS.docx since that's what user created
    template = templates_dir / 'UGS.docx'
    if template.exists():
        extract_template_content(template)
    else:
        print(f"❌ Template not found: {template}")
