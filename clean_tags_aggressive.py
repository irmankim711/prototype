"""
Aggressively clean all Jinja2 tags to remove line breaks and normalize spacing
"""
from docx import Document
import re

def clean_all_tags(input_path, output_path):
    """Clean all Jinja2 tags by removing internal line breaks"""
    doc = Document(input_path)
    fixes = 0

    # Process all paragraphs in the document
    for paragraph in doc.paragraphs:
        original_text = paragraph.text
        if '{{' in original_text and '}}' in original_text:
            # Reconstruct the paragraph without line breaks inside tags
            new_text = original_text

            # Find all {{ ... }} blocks and remove line breaks within them
            def clean_tag(match):
                tag_content = match.group(1)
                # Remove all line breaks and normalize spaces
                cleaned = ' '.join(tag_content.split())
                return '{{ ' + cleaned + ' }}'

            new_text = re.sub(r'\{\{(.*?)\}\}', clean_tag, new_text, flags=re.DOTALL)

            if new_text != original_text:
                # Clear all runs and set new text
                paragraph.clear()
                paragraph.add_run(new_text)
                fixes += 1
                print(f"Para fixed: {repr(original_text[:50])} -> {repr(new_text[:50])}")

    # Process all tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    original_text = paragraph.text
                    if '{{' in original_text and '}}' in original_text:
                        new_text = original_text

                        def clean_tag(match):
                            tag_content = match.group(1)
                            cleaned = ' '.join(tag_content.split())
                            return '{{ ' + cleaned + ' }}'

                        new_text = re.sub(r'\{\{(.*?)\}\}', clean_tag, new_text, flags=re.DOTALL)

                        if new_text != original_text:
                            paragraph.clear()
                            paragraph.add_run(new_text)
                            fixes += 1
                            print(f"Cell fixed: {repr(original_text[:50])} -> {repr(new_text[:50])}")

    doc.save(output_path)
    print(f"\n✅ Cleaned {fixes} tags")
    return fixes

if __name__ == "__main__":
    input_file = "backend/templates/04- LAPORAN FU _ PUNCAK ALAM_converted.docx"
    output_file = "backend/templates/04- LAPORAN FU _ PUNCAK ALAM_final.docx"

    print("Cleaning all tags...\n")
    fixes = clean_all_tags(input_file, output_file)

    # Verify
    print("\n🔍 Final verification...")
    doc = Document(output_file)
    tags = set()

    for p in doc.paragraphs:
        for tag in re.findall(r'\{\{\s*([^}]+?)\s*\}\}', p.text):
            tags.add(tag)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text
                for tag in re.findall(r'\{\{\s*([^}]+?)\s*\}\}', text):
                    tags.add(tag)

    print(f"\nFinal Jinja2 tags (cleaned):")
    for tag in sorted(tags):
        print(f"  {{{{ {tag} }}}}")
    print(f"\nTotal unique tags: {len(tags)}")

    # Check for any remaining line breaks in tags
    print("\n🔍 Checking for line breaks in tags...")
    has_linebreaks = False
    for tag in tags:
        if '\n' in tag or '\r' in tag:
            print(f"  ⚠️  Tag still has line break: {repr(tag)}")
            has_linebreaks = True

    if not has_linebreaks:
        print("  ✅ No line breaks found in any tags!")
