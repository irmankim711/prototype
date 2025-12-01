import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath("c:/Users/IRMAN/OneDrive/Desktop/prototype/backend"))

try:
    from app import create_app
    app = create_app()
    with app.app_context():
        # Trigger route registration
        from app.routes import nextgen_report_builder
        print("✅ Routes imported successfully")
except Exception as e:
    print(f"❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
