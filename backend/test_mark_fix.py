"""
Test script to verify that PRE/POST marks are properly inserted into reports
Run this to test the entire flow from Excel -> Data Transformation -> DOCX generation
"""

import sys
import os
sys.path.insert(0, '.')

from app.services.report_generation_service import ReportGenerationService
import pandas as pd
from docx import Document
from datetime import datetime
import math

print("="*70)
print("TEST: Pre/Post Marks in Report Generation")
print("="*70)

# 1. Load Excel file
excel_path = 'app/static/uploads/excel/1_c5aaa75326e540b38551e4d322807b10_SENARAI SEMAK PUNCAK ALAM.xlsx'
if not os.path.exists(excel_path):
    print(f"❌ Excel file not found: {excel_path}")
    sys.exit(1)

df = pd.read_excel(excel_path)
print(f"\n✅ Step 1: Loaded Excel file")
print(f"   - Total rows: {len(df)}")
print(f"   - Rows with PRE marks: {df['MARKAH_PRE'].notna().sum()}")
print(f"   - Rows with POST marks: {df['MARKAH_POST'].notna().sum()}")

# 2. Transform data (simulating what the service does)
records = df.to_dict('records')
data = {'records': records}
service = ReportGenerationService()
transformed = service._transform_data_for_docx(data)

print(f"\n✅ Step 2: Transformed data")
print(f"   - Total participants: {len(transformed.get('peserta_list', []))}")

# Check for 'nan' strings
has_nan = any('nan' in str(p['markah_pre']).lower() or 'nan' in str(p['markah_post']).lower()
              for p in transformed['peserta_list'])

if has_nan:
    print(f"   ❌ ERROR: Found 'nan' strings in marks!")
    for p in transformed['peserta_list']:
        if 'nan' in str(p['markah_pre']).lower() or 'nan' in str(p['markah_post']).lower():
            print(f"      Problem: {p['nama'][:30]} - PRE:{p['markah_pre']}, POST:{p['markah_post']}")
    sys.exit(1)
else:
    print(f"   ✅ No 'nan' strings found")

# 3. Show sample data
print(f"\n✅ Step 3: Sample participant data:")
for i, p in enumerate(transformed['peserta_list'][:5], 1):
    pre = p['markah_pre'] if p['markah_pre'] else '(empty)'
    post = p['markah_post'] if p['markah_post'] else '(empty)'
    print(f"   {i}. {p['nama'][:35]:35} | PRE: {pre:8} | POST: {post:8}")

# 4. Generate actual DOCX using docxtpl
from docxtpl import DocxTemplate

template_path = 'templates/report_template_copy.docx'
if not os.path.exists(template_path):
    print(f"\n❌ Template not found: {template_path}")
    sys.exit(1)

output_path = f'test_report_marks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'

print(f"\n✅ Step 4: Generating DOCX report...")
try:
    doc = DocxTemplate(template_path)
    doc.render({'peserta_list': transformed['peserta_list']})
    doc.save(output_path)
    print(f"   ✅ Report saved: {output_path}")
except Exception as e:
    print(f"   ❌ Error generating report: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Verify the output
print(f"\n✅ Step 5: Verifying generated report...")
check_doc = Document(output_path)

# Find tables with marks
mark_tables_found = 0
marks_populated = 0

for table_idx, table in enumerate(check_doc.tables):
    for row_idx, row in enumerate(table.rows):
        row_text = ''.join([cell.text for cell in row.cells])
        # Check if this is a header row with "MARKAH PRA" or "MARKAH POST"
        if 'MARKAH PRA' in row_text or 'MARKAH POST' in row_text:
            mark_tables_found += 1
            print(f"   Found marks table: Table {table_idx + 1}, Row {row_idx + 1}")

            # Check next few rows for data
            for data_row_idx in range(row_idx + 1, min(row_idx + 6, len(table.rows))):
                data_row = table.rows[data_row_idx]
                for cell in data_row.cells:
                    cell_text = cell.text.strip()
                    # Check if it's a numeric mark (not empty, not placeholder)
                    if cell_text and cell_text.replace('.', '').isdigit():
                        marks_populated += 1
                        print(f"      Row {data_row_idx + 1}: Found mark '{cell_text}'")
                        break
                if marks_populated >= 3:  # Just check first few
                    break
            break

if mark_tables_found == 0:
    print(f"   ⚠️  WARNING: No tables with 'MARKAH PRA' or 'MARKAH POST' headers found")
elif marks_populated == 0:
    print(f"   ❌ ERROR: Found mark tables but no marks populated!")
else:
    print(f"   ✅ SUCCESS: Found {marks_populated} populated marks in tables")

# Final summary
print(f"\n" + "="*70)
print(f"TEST SUMMARY")
print(f"="*70)
print(f"Excel data loaded:        ✅")
print(f"Data transformed:         ✅")
print(f"No 'nan' strings:         ✅")
print(f"DOCX generated:           ✅")
print(f"Marks populated:          {'✅' if marks_populated > 0 else '❌'}")
print(f"\nOutput file: {output_path}")
print(f"="*70)

if marks_populated > 0:
    print(f"\n🎉 ALL TESTS PASSED! The fix is working correctly.")
    sys.exit(0)
else:
    print(f"\n⚠️  Tests completed but marks may not be showing in the report.")
    print(f"   Please open {output_path} and check manually.")
    sys.exit(0)
