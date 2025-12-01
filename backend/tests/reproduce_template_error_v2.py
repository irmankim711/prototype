import sys
import os
from pathlib import Path
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.services.report_generation_service import report_generation_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_template_lookup():
    app = create_app('testing')
    with app.app_context():
        print("Testing template lookup for 'uwais_global_solution'...")
        try:
            template_file, db_record = report_generation_service._get_template(
                request_id="test_req",
                template_id="uwais_global_solution",
                user_id=1
            )
            print(f"Result: {template_file}")
            if template_file and template_file.exists():
                print("✅ Template found successfully!")
            else:
                print("❌ Template NOT found.")
        except Exception as e:
            print(f"❌ Error during lookup: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import app.models
    print(f"DEBUG: app.models.GeneratedReport = {getattr(app.models, 'GeneratedReport', 'NOT FOUND')}")
    test_template_lookup()
