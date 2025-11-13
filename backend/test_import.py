#!/usr/bin/env python3
"""
Test if the module can be imported without errors
"""
import sys
import os

# Add the backend directory to the path
backend_dir = r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend"
sys.path.insert(0, backend_dir)

print("="*80)
print("IMPORT TEST")
print("="*80)

try:
    # Set up minimal environment
    os.environ.setdefault('FLASK_APP', 'app')

    print("Attempting to import the module...")

    # Try to import
    from app.routes import nextgen_report_builder

    print("✓ Module imported successfully - NO SYNTAX ERRORS")
    print(f"✓ Module path: {nextgen_report_builder.__file__}")

    # List some functions/classes to verify it loaded
    print(f"\nModule contains these items:")
    items = [name for name in dir(nextgen_report_builder) if not name.startswith('_')]
    for item in items[:20]:  # Show first 20
        print(f"  - {item}")

    sys.exit(0)

except SyntaxError as e:
    print("✗ SYNTAX ERROR during import:")
    print(f"  File: {e.filename}")
    print(f"  Line: {e.lineno}")
    print(f"  Column: {e.offset}")
    print(f"  Error: {e.msg}")
    print(f"  Text: {e.text}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

except Exception as e:
    print(f"✗ Error during import (not a syntax error):")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
