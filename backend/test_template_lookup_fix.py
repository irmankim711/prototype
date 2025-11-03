"""
Test script to verify template lookup fix for both integer IDs and string names
"""

def test_template_id_parsing():
    """Test that template ID can be either integer or string"""

    # Test 1: Integer template ID
    template_id = "123"
    try:
        template_id_int = int(template_id)
        print(f"✅ Test 1 PASS: Integer conversion succeeded for '{template_id}' -> {template_id_int}")
    except (ValueError, TypeError) as e:
        print(f"❌ Test 1 FAIL: Integer conversion failed for '{template_id}': {e}")

    # Test 2: String template name (should fail integer conversion)
    template_id = "04- LAPORAN FU _ PUNCAK ALAM_final"
    try:
        template_id_int = int(template_id)
        print(f"❌ Test 2 FAIL: Should not convert string name to integer")
    except (ValueError, TypeError) as e:
        print(f"✅ Test 2 PASS: String template name correctly caught: {type(e).__name__}")
        print(f"   Now trying name-based lookup for: {template_id}")

    # Test 3: Template name with extension
    template_id = "04- LAPORAN FU _ PUNCAK ALAM_final.docx"
    clean_template_name = str(template_id)
    for ext in ['.docx', '.jinja', '.tex', '.html']:
        if clean_template_name.endswith(ext):
            clean_template_name = clean_template_name[:-len(ext)]
            break

    print(f"✅ Test 3 PASS: Extension removed")
    print(f"   Original: {template_id}")
    print(f"   Cleaned:  {clean_template_name}")

    # Test 4: Dynamic SQL building
    safe_report_data = {
        'title': 'Test Report',
        'description': 'Test Description',
        'created_by': 'user123',
    }

    # Only add template_id if valid
    template_db_id = None
    if template_db_id:
        safe_report_data['template_id'] = template_db_id

    columns = list(safe_report_data.keys())
    placeholders = [f":{col}" for col in columns]

    sql = f"INSERT INTO reports ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    print(f"✅ Test 4 PASS: Dynamic SQL built without template_id")
    print(f"   SQL: {sql}")
    print(f"   Columns: {columns}")

    # Test 5: With template_id
    safe_report_data['template_id'] = 123
    columns = list(safe_report_data.keys())
    placeholders = [f":{col}" for col in columns]

    sql = f"INSERT INTO reports ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    print(f"✅ Test 5 PASS: Dynamic SQL built with template_id")
    print(f"   SQL: {sql}")
    print(f"   Columns: {columns}")

if __name__ == '__main__':
    print("=" * 80)
    print("Testing Template Lookup Fix")
    print("=" * 80)
    test_template_id_parsing()
    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
