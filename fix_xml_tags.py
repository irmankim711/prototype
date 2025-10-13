"""
Fix tags by working at the XML level to handle split runs
"""
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import qn
import re
import zipfile
import os
import shutil

def fix_template_xml(input_path, output_path):
    """Fix template by working with the raw XML to merge split runs"""

    # First, let's use a simpler approach - just rename the variables
    # to not include line breaks
    doc = Document(input_path)

    # Define the mappings for problematic tags
    replacements = {
        'KEHADIRAH \n(SABTU)': 'KEHADIRAH_SABTU',
        'KEHADIRAN\n(AHAD)': 'KEHADIRAN_AHAD',
        'KEHADIRAH\n(SABTU)': 'KEHADIRAH_SABTU',
        'KEHADIRAN \n(AHAD)': 'KEHADIRAN_AHAD',
    }

    fixes = 0

    # Process tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    text = paragraph.text

                    # Check if this paragraph contains problematic tags
                    for old_tag, new_tag in replacements.items():
                        if old_tag in text:
                            # Replace in the actual text
                            new_text = text.replace(old_tag, new_tag)
                            paragraph.clear()
                            paragraph.add_run(new_text)
                            fixes += 1
                            print(f"Replaced: {repr(old_tag)} -> {repr(new_tag)}")

    doc.save(output_path)
    print(f"\n✅ Made {fixes} replacements")
    return fixes

if __name__ == "__main__":
    input_file = "backend/templates/04- LAPORAN FU _ PUNCAK ALAM_converted.docx"
    output_file = "backend/templates/04- LAPORAN FU _ PUNCAK ALAM_final.docx"

    print("Fixing tags at XML level...\n")
    fixes = fix_template_xml(input_file, output_file)

    # Verify
    print("\n🔍 Final verification...")
    doc = Document(output_file)
    tags = set()

    for p in doc.paragraphs:
        for tag in re.findall(r'\{\{\s*([^}]+?)\s*\}\}', p.text):
            tags.add(tag.strip())

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for tag in re.findall(r'\{\{\s*([^}]+?)\s*\}\}', cell.text):
                    tags.add(tag.strip())

    print(f"\n✅ Final Jinja2 tags:")
    for tag in sorted(tags):
        print(f"  {{{{ {tag} }}}}")
    print(f"\nTotal: {len(tags)} tags")

    # Check for line breaks
    has_breaks = any('\n' in tag or '\r' in tag for tag in tags)
    if has_breaks:
        print("\n⚠️  Some tags still have line breaks")
    else:
        print("\n✅ All tags are clean!")
