#!/usr/bin/env python3
"""
Test report creation to identify the exact error
"""

import os
import sys
import traceback

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_report_creation():
    """Test creating a report to see the exact error"""
    
    print("🧪 TESTING REPORT CREATION")
    print("=" * 40)
    
    try:
        # Import Flask app
        from app import create_app, db
        
        print("✅ Flask app imported successfully")
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            print("✅ App context created")
            
            # Try to import Report model
            try:
                from app.models import Report
                print("✅ Report model imported from app.models")
                model_source = "app.models"
            except ImportError as e:
                print(f"⚠️ Could not import from app.models: {e}")
                try:
                    from app.models.production.report_models import Report
                    print("✅ Report model imported from production.report_models")
                    model_source = "production.report_models"
                except ImportError as e2:
                    print(f"❌ Could not import from production models: {e2}")
                    return False
            
            # Check model fields
            print(f"\n📋 Report model fields (from {model_source}):")
            for column in Report.__table__.columns:
                print(f"   • {column.name}: {column.type}")
            
            # Try to create a test report
            print(f"\n🔄 Testing report creation...")
            
            test_report = Report(
                title="Test Report",
                description="Test description",
                report_type="test"
            )
            
            # Check if status field exists on the model
            if hasattr(test_report, 'status'):
                print("✅ Model has 'status' field")
                test_report.status = "generated"
            elif hasattr(test_report, 'generation_status'):
                print("✅ Model has 'generation_status' field")
                test_report.generation_status = "generated"
            else:
                print("❌ Model has neither 'status' nor 'generation_status' field")
            
            # Try to add to database
            try:
                db.session.add(test_report)
                db.session.commit()
                print("✅ Report created successfully!")
                
                # Clean up
                db.session.delete(test_report)
                db.session.commit()
                print("✅ Test report cleaned up")
                
                return True
                
            except Exception as db_error:
                print(f"❌ Database error: {db_error}")
                print(f"Full traceback:")
                traceback.print_exc()
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Full traceback:")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success = test_report_creation()
    
    if success:
        print(f"\n🎉 REPORT CREATION TEST PASSED!")
        print(f"The issue is likely elsewhere in the code.")
    else:
        print(f"\n❌ REPORT CREATION TEST FAILED!")
        print(f"This confirms the database schema mismatch issue.")

if __name__ == '__main__':
    main()
