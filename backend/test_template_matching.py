"""
Test template fuzzy matching logic
"""
from pathlib import Path

# Simulate the fuzzy matching logic
template_id = "04- Laporan Fu   Puncak Alam Final"
templates_dir = Path("templates")

print(f"Looking for template: {repr(template_id)}")
print(f"Templates directory: {templates_dir}\n")

# Normalize the template_id for fuzzy matching
normalized_id = template_id.lower().replace('_', '').replace(' ', '').replace('-', '')
print(f"Normalized ID: {repr(normalized_id)}\n")

# Check available templates
if templates_dir.exists():
    print("Available templates:")
    for template_path in templates_dir.iterdir():
        if template_path.is_file():
            print(f"  - {template_path.name}")
            normalized_filename = template_path.name.lower().replace('_', '').replace(' ', '').replace('-', '')
            print(f"    Normalized: {repr(normalized_filename)}")

            # Check if it matches
            if normalized_id in normalized_filename or normalized_filename.startswith(normalized_id):
                print(f"    ✅ MATCH!")
            else:
                print(f"    ❌ No match")
            print()
else:
    print("Templates directory not found!")
