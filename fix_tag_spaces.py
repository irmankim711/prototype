"""
Replace spaces with underscores in Jinja2 tags
Jinja2 variable names cannot contain spaces
"""
from docx import Document
import re

def fix_tag_spaces(input_path, output_path):
    """Replace spaces in tag names with underscores"""
    doc = Document(input_path)
    fixes = 0

    print("Fixing spaces in tag names...\n")

    # Process tables
    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para_idx, paragraph in enumerate(cell.paragraphs):
                    original_text = paragraph.text

                    # Find tags with spaces and replace spaces with underscores
                    def fix_tag(match):
                        tag_content = match.group(1).strip()
                        fixed_tag = tag_content.replace(' ', '_')
                        if tag_content != fixed_tag:
                            print(f"  Table {table_idx}, Cell ({row_idx},{cell_idx}): {tag_content} → {fixed_tag}")
                        return '{{ ' + fixed_tag + ' }}'

                    new_text = re.sub(r'\{\{\s*([^}]+?)\s*\}\}', fix_tag, original_text)

                    if new_text != original_text:
                        paragraph.clear()
                        paragraph.add_run(new_text)
                        fixes += 1

    # Process paragraphs
    for paragraph in doc.paragraphs:
        original_text = paragraph.text

        def fix_tag(match):
            tag_content = match.group(1).strip()
            fixed_tag = tag_content.replace(' ', '_')
            return '{{ ' + fixed_tag + ' }}'

        new_text = re.sub(r'\{\{\s*([^}]+?)\s*\}\}', fix_tag, original_text)

        if new_text != original_text:
            paragraph.clear()
            paragraph.add_run(new_text)
            fixes += 1

    doc.save(output_path)
    print(f"\n✅ Fixed {fixes} tags")
    return fixes

if __name__ == "__main__":
    input_file = "backend/templates/04- LAPORAN FU _ PUNCAK ALAM_final.docx"
    output_file = "backend/templates/04- LAPORAN FU _ PUNCAK ALAM_final.docx"

    fixes = fix_tag_spaces(input_file, output_file)

    # Verify
    print("\n🔍 Final verification...")
    doc = Document(output_file)
    tags = set()

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for tag in re.findall(r'\{\{\s*([^}]+?)\s*\}\}', cell.text):
                    tags.add(tag.strip())

    print(f"\n✅ All Jinja2 tags (final):")
    for tag in sorted(tags):
        print(f"  {{{{ {tag} }}}}")

    # Check for spaces
    tags_with_spaces = [t for t in tags if ' ' in t]
    if tags_with_spaces:
        print(f"\n⚠️  {len(tags_with_spaces)} tags still have spaces:")
        for tag in tags_with_spaces:
            print(f"    {tag}")
    else:
        print(f"\n✅ All {len(tags)} tags are valid (no spaces)!")
