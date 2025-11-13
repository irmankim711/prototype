import ast
import sys
import re

def find_all_syntax_errors(filepath):
    """Comprehensive syntax error detection"""
    errors = []

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Method 1: Try to parse with AST
    print("=" * 80)
    print("METHOD 1: AST Parser")
    print("=" * 80)
    try:
        ast.parse(content)
        print("✓ No AST syntax errors found")
    except SyntaxError as e:
        print(f"✗ SYNTAX ERROR at line {e.lineno}:")
        print(f"  Error: {e.msg}")
        if e.text:
            print(f"  Text: {e.text.strip()}")
        print(f"  Offset: {e.offset}")
        errors.append({
            'line': e.lineno,
            'error': e.msg,
            'text': e.text
        })

    # Method 2: Search for unterminated f-strings
    print("\n" + "=" * 80)
    print("METHOD 2: Pattern-based f-string detection")
    print("=" * 80)

    # Pattern for f-strings that might be unterminated
    fstring_patterns = [
        (r'f"[^"]*\{[^}]*$', 'Possible unterminated f-string with {'),
        (r"f'[^']*\{[^}]*$", 'Possible unterminated f-string with {'),
        (r'f"""[^"]*\{[^}]*$', 'Possible unterminated triple-quote f-string'),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, desc in fstring_patterns:
            if re.search(pattern, line):
                print(f"Line {i}: {desc}")
                print(f"  Content: {line.strip()}")

    # Method 3: Check for unbalanced quotes
    print("\n" + "=" * 80)
    print("METHOD 3: Quote balance check")
    print("=" * 80)

    in_triple_single = False
    in_triple_double = False
    in_single = False
    in_double = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Count quotes (simplified - not perfect but catches many issues)
        triple_double = line.count('"""')
        triple_single = line.count("'''")

        if triple_double % 2 != 0:
            print(f"Line {i}: Odd number of triple-double quotes")
            print(f"  Content: {line.strip()}")

        if triple_single % 2 != 0:
            print(f"Line {i}: Odd number of triple-single quotes")
            print(f"  Content: {line.strip()}")

    # Method 4: Check specific problematic lines
    print("\n" + "=" * 80)
    print("METHOD 4: Checking specific lines (832, 1502)")
    print("=" * 80)

    for line_num in [832, 1502]:
        if line_num <= len(lines):
            print(f"\nLine {line_num}:")
            # Show context
            start = max(0, line_num - 3)
            end = min(len(lines), line_num + 3)
            for i in range(start, end):
                marker = ">>>" if i + 1 == line_num else "   "
                print(f"{marker} {i+1:5d}: {lines[i]}")

    # Method 5: Try to find all unclosed strings
    print("\n" + "=" * 80)
    print("METHOD 5: Detailed line-by-line analysis")
    print("=" * 80)

    problematic_lines = []
    for i, line in enumerate(lines, 1):
        # Skip comments and empty lines
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Look for f-strings with opening braces but possibly not closed
        if 'f"' in line or "f'" in line:
            # Check if there are unmatched braces in f-strings
            if '{' in line:
                # Very simple check - count braces
                open_braces = line.count('{')
                close_braces = line.count('}')
                if open_braces > close_braces:
                    problematic_lines.append((i, line, f"More open {{ than close }} braces"))

    if problematic_lines:
        print(f"Found {len(problematic_lines)} lines with potential brace imbalance:")
        for line_num, line_content, issue in problematic_lines[:20]:  # Show first 20
            print(f"  Line {line_num}: {issue}")
            print(f"    {line_content.strip()[:100]}")
    else:
        print("No obvious brace imbalance issues found")

    return errors

if __name__ == "__main__":
    filepath = r"c:\Users\IRMAN\OneDrive\Desktop\prototype\backend\app\routes\nextgen_report_builder.py"
    find_all_syntax_errors(filepath)
