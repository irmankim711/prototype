import sys
import os
from pathlib import Path
import logging
import openpyxl

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.services.report_generation_service import report_generation_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dummy_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["Name", "Age", "City"])
    ws.append(["Alice", 30, "New York"])
    ws.append(["Bob", 25, "Los Angeles"])
    path = Path("dummy_data.xlsx")
    wb.save(path)
    return str(path.resolve())

def test_generation():
    app = create_app('testing')
    with app.app_context():
        print("Testing full report generation...")
        excel_path = create_dummy_excel()
        try:
            result = report_generation_service.generate_report(
                user_id=1,
                template_id="uwais_global_solution",
                excel_file_path=excel_path,
                report_title="Test Report"
            )
            print(f"Result: {result}")
            if result['success']:
                print("✅ Generation successful!")
            else:
                print(f"❌ Generation failed: {result.get('error')}")
                print(f"Details: {result.get('details')}")
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if os.path.exists(excel_path):
                os.remove(excel_path)

if __name__ == "__main__":
    test_generation()
