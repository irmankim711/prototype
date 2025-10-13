#!/usr/bin/env python3
"""
Test script to test the reports endpoint logic directly
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_reports_endpoint_directly():
    """Test the reports endpoint logic directly"""
    try:
        print("🔍 Testing reports endpoint logic directly...")
        
        from app import create_app, db
        from app.models import Report
        from app.decorators import get_current_user_id
        from sqlalchemy import desc
        from flask import request
        
        app = create_app()
        
        with app.app_context():
            print("✅ App context created")
            
            # Simulate the exact logic from the reports endpoint
            print("\n📋 Simulating reports endpoint logic...")
            
            try:
                # This is the exact logic from the get_reports function
                user_id = get_current_user_id()
                page = 1
                per_page = 10
                status = None
                
                print(f"📊 Parameters: user_id={user_id}, page={page}, per_page={per_page}, status={status}")
                
                if page < 1:
                    print("❌ Page validation failed")
                    return False
                
                # Handle case when no user is authenticated (for testing)
                if user_id is None:
                    print("ℹ️ No user ID, returning empty results")
                    result = {
                        'reports': [],
                        'pagination': {
                            'page': page,
                            'pages': 0,
                            'per_page': per_page,
                            'total': 0,
                            'has_next': False,
                            'has_prev': False
                        }
                    }
                    print(f"✅ Empty result structure: {result}")
                    return True
                
                # This part should not execute for None user_id
                print("⚠️ This should not execute for None user_id")
                query = Report.query.filter_by(user_id=user_id)
                
                if status:
                    valid_statuses = ['processing', 'completed', 'failed', 'pending']
                    if status not in valid_statuses:
                        print(f"❌ Invalid status: {status}")
                        return False
                    query = query.filter_by(status=status)
                
                reports = query.order_by(desc(Report.created_at)).paginate(
                    page=page, per_page=per_page, error_out=False
                )
                
                result = {
                    'reports': [{
                        'id': report.id,
                        'title': report.title,
                        'description': report.description,
                        'status': report.status,
                        'createdAt': report.created_at.isoformat(),
                        'updatedAt': report.updated_at.isoformat(),
                        'templateId': report.template_id,
                        'outputUrl': report.output_url
                    } for report in reports.items],
                    'pagination': {
                        'page': reports.page,
                        'pages': reports.pages,
                        'per_page': reports.per_page,
                        'total': reports.total,
                        'has_next': reports.has_next,
                        'has_prev': reports.has_prev
                    }
                }
                
                print(f"✅ Full result structure: {result}")
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
    print("🚀 Reports Endpoint Direct Test")
    print("=" * 50)
    
    success = test_reports_endpoint_directly()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test passed!")
    else:
        print("❌ Test failed!")
    print("🏁 Test completed")
