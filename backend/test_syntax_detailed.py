#!/usr/bin/env python3
"""
Detailed syntax error checker for nextgen_report_builder.py
"""
import sys
import traceback

def check_syntax_by_compilation():
    """Try to compile the file and catch any syntax errors"""
    filepath = r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\routes\nextgen_report_builder.py"

    print("="*80)
    print("COMPILATION TEST")
    print("="*80)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Try to compile
        compile(source_code, filepath, 'exec')
        print("✓ File compiles successfully - NO SYNTAX ERRORS FOUND")
        return True

    except SyntaxError as e:
        print("✗ SYNTAX ERROR DETECTED:")
        print(f"  File: {e.filename}")
        print(f"  Line: {e.lineno}")
        print(f"  Column: {e.offset}")
        print(f"  Error: {e.msg}")
        print(f"  Text: {e.text}")
        print()
        print("Full traceback:")
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

def check_specific_lines():
    """Check specific lines that were identified as problematic"""
    filepath = r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\routes\nextgen_report_builder.py"

    print("\n" + "="*80)
    print("SPECIFIC LINE ANALYSIS")
    print("="*80)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Check line 1502 (array index 1501)
    print("\n--- Line 1502 and context ---")
    for i in range(1498, min(1510, len(lines))):
        marker = ">>> " if i == 1501 else "    "
        print(f"{marker}{i+1:5d}: {lines[i]}", end='')

    # Analyze the string
    print("\n\nAnalysis of line 1502:")
    line_1502 = lines[1501]
    print(f"Raw: {repr(line_1502)}")
    print(f"Stripped: {repr(line_1502.strip())}")

    # Check if it's part of a multi-line string
    print("\nChecking if this is part of a multi-line f-string...")
    if line_1502.strip().startswith('f"'):
        print("  - Starts with f-string opener")
        if '{' in line_1502 and '}' not in line_1502:
            print("  - Contains opening { but no closing }")
            print("  - This appears to be a MULTI-LINE f-string")

            # Check next lines
            print("\n  Looking at continuation...")
            for i in range(1502, min(1510, len(lines))):
                print(f"    {i+1:5d}: {lines[i]}", end='')
                if '}' in lines[i]:
                    print(f"    Found closing }} on line {i+1}")
                    break

    # Check line 3388
    print("\n\n--- Line 3388 and context ---")
    for i in range(3384, min(3398, len(lines))):
        marker = ">>> " if i == 3387 else "    "
        print(f"{marker}{i+1:5d}: {lines[i]}", end='')

    print("\n\nAnalysis of line 3388:")
    line_3388 = lines[3387]
    print(f"Raw: {repr(line_3388)}")
    print(f"Stripped: {repr(line_3388.strip())}")

    # This looks like a dictionary assignment
    if '{' in line_3388 and '}' not in line_3388:
        print("  - This is a dictionary literal opening")
        print("  - NOT a syntax error - this is valid Python (multi-line dict)")

if __name__ == "__main__":
    success = check_syntax_by_compilation()
    check_specific_lines()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    if success:
        print("✓ No actual syntax errors found")
        print("✓ The patterns detected were FALSE POSITIVES")
        print("  - Line 1502: Multi-line f-string (valid)")
        print("  - Line 3388: Multi-line dictionary (valid)")
    else:
        print("✗ Syntax errors exist - see details above")

    sys.exit(0 if success else 1)
