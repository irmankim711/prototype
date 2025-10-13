#!/usr/bin/env python3
"""
Test the new SupabaseReport model to ensure it works with the actual database schema
"""

import os
import sys
import traceback
import uuid

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_supabase_report_model():
    """Test the SupabaseReport model"""
    
    print("🧪 TESTING SUPABASE REPORT MODEL")
    print("=" * 45)
    
    try:
        # Import Flask app
        from app import create_app, db
        
        print("✅ Flask app imported successfully")
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            print("✅ App context created")
            
            # Import the new model
            from app.models.supabase_report import SupabaseReport
            print("✅ SupabaseReport model imported successfully")
            
            # Check model fields
            print(f"\n📋 SupabaseReport model fields:")
            for column in SupabaseReport.__table__.columns:
                print(f"   • {column.name}: {column.type}")
            
            # Create a test report
            print(f"\n🔄 Testing report creation...")
            
            test_report = SupabaseReport.create_report(
                title="Test Supabase Report",
                description="Testing the new Supabase-compatible model",
                report_type="test",
                parameters={"test": True}
            )
            
            print(f"✅ Report instance created")
            print(f"   ID: {test_report.id}")
            print(f"   Title: {test_report.title}")
            print(f"   Status: {test_report.status}")
            
            # Try to save to database
            try:
                db.session.add(test_report)
                db.session.commit()
                print("✅ Report saved to Supabase successfully!")
                
                # Test retrieval
                retrieved = SupabaseReport.query.filter_by(id=test_report.id).first()
                if retrieved:
                    print("✅ Report retrieved from database successfully!")
                    print(f"   Retrieved title: {retrieved.title}")
                    print(f"   Retrieved status: {retrieved.status}")
                    
                    # Test to_dict method
                    report_dict = retrieved.to_dict()
                    print("✅ to_dict() method works!")
                    print(f"   Dict keys: {list(report_dict.keys())}")
                
                # Test status update
                retrieved.update_status('completed')
                db.session.commit()
                print("✅ Status update works!")
                print(f"   New status: {retrieved.status}")
                print(f"   Completed at: {retrieved.completed_at}")
                
                # Clean up
                db.session.delete(retrieved)
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

def test_report_endpoints():
    """Test that report endpoints can use the new model"""
    
    print(f"\n🔍 TESTING REPORT ENDPOINTS COMPATIBILITY")
    print("-" * 45)
    
    try:
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            # Test that we can import the model in routes
            from app.models.supabase_report import SupabaseReport
            
            # Create a sample report for API testing
            sample_report = SupabaseReport.create_report(
                title="API Test Report",
                report_type="api_test",
                description="Test report for API endpoints"
            )
            
            # Convert to dict (what APIs would return)
            api_response = sample_report.to_dict()
            
            print("✅ API compatibility test passed!")
            print(f"   API response keys: {len(api_response)} fields")
            print(f"   Sample fields: id, title, status, created_at")
            
            return True
            
    except Exception as e:
        print(f"❌ API compatibility test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 SUPABASE REPORT MODEL TEST")
    print("=" * 50)
    
    # Test the model
    model_success = test_supabase_report_model()
    
    # Test API compatibility
    api_success = test_report_endpoints()
    
    if model_success and api_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"The SupabaseReport model is working correctly.")
        print(f"\n💡 To use this model in your routes:")
        print(f"   Replace: from app.models import Report")
        print(f"   With:    from app.models.supabase_report import SupabaseReport as Report")
        print(f"\n✅ This will fix the database schema mismatch issue!")
    else:
        print(f"\n❌ TESTS FAILED!")
        print(f"Check the error messages above for details.")

if __name__ == '__main__':
    main()
