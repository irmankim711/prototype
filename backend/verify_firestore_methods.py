import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath("c:/Users/IRMAN/OneDrive/Desktop/prototype/backend"))

try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.services.firestore_report_service import firestore_report_service
        print("✅ FirestoreReportService initialized")
        
        if hasattr(firestore_report_service, 'create_report'):
             print("✅ create_report method exists")
        else:
             print("❌ create_report method MISSING")

        if hasattr(firestore_report_service, 'save_report_file'):
             print("✅ save_report_file method exists")
        else:
             print("❌ save_report_file method MISSING")
             
except Exception as e:
    print(f"❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
