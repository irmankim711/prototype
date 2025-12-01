
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Testing imports...")
    from app.services.report_generation_service import report_generation_service
    print("✅ ReportGenerationService imported successfully")
    
    print("Testing service instantiation...")
    assert report_generation_service is not None
    print("✅ Service instance exists")
    
    print("Testing method existence...")
    assert hasattr(report_generation_service, 'generate_report')
    print("✅ generate_report method exists")
    
    print("All checks passed!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Verification failed: {e}")
    sys.exit(1)
