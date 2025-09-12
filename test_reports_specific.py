#!/usr/bin/env python3
"""
Test script to debug the specific reports endpoint logic
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_reports_logic():
    """Test the reports endpoint logic step by step"""
    try:
        print("🔍 Testing reports endpoint logic...")
        
        from app import create_app, db
        from app.models import Report
        from app.decorators import get_current_user_id
        from sqlalchemy import desc
        
        app = create_app()
        
        with app.app_context():
            print("✅ App context created")
            
            # Test 1: Check if get_current_user_id works
            print("\n📋 Test 1: get_current_user_id function")
            try:
                user_id = get_current_user_id()
                print(f"✅ get_current_user_id returned: {user_id}")
            except Exception as e:
                print(f"❌ get_current_user_id failed: {e}")
                return False
            
            # Test 2: Check if Report model can be queried
            print("\n📋 Test 2: Report model query")
            try:
                # Try to get total count
                total_reports = Report.query.count()
                print(f"✅ Total reports in database: {total_reports}")
                
                # Try to get a sample report
                sample_report = Report.query.first()
                if sample_report:
                    print(f"✅ Sample report found: ID {sample_report.id}, Title: {sample_report.title}")
                else:
                    print("ℹ️ No reports found in database")
                    
            except Exception as e:
                print(f"❌ Report query failed: {e}")
                return False
            
            # Test 3: Test the specific query logic from the endpoint
            print("\n📋 Test 3: Endpoint query logic")
            try:
                user_id = get_current_user_id()
                page = 1
                per_page = 10
                
                if user_id is None:
                    print("ℹ️ No user ID, returning empty results")
                    return True
                
                query = Report.query.filter_by(user_id=user_id)
                print(f"✅ Query created for user_id: {user_id}")
                
                # Test pagination
                reports = query.order_by(desc(Report.created_at)).paginate(
                    page=page, per_page=per_page, error_out=False
                )
                print(f"✅ Pagination successful - Page {reports.page}, Total: {reports.total}")
                
                return True
                
            except Exception as e:
                print(f"❌ Endpoint logic failed: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Reports Endpoint Logic Test")
    print("=" * 50)
    
    success = test_reports_logic()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("🏁 Test completed")
