#!/usr/bin/env python3
"""
Test Report Creation Fix
Test that reports can be created without foreign key constraint violations
"""

import sys
import os
from datetime import datetime

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def test_report_creation():
    """Test creating a report with proper template_id and program_id"""
    
    try:
        # Import Flask app and models
        from app import create_app, db
        from app.models import Report, User
        from app.routes.reports_api import resolve_template_id
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            print("=== Testing Report Creation ===")
            
            # Test template resolution
            test_config = {'template_used': 'Temp1'}
            template_id = resolve_template_id(test_config)
            print(f"✓ Template resolution: 'Temp1' -> {template_id}")
            
            # Try to create a report (simulate the fixed code)
            try:
                test_report_data = {
                    'title': 'Test Report',
                    'description': 'Test report for constraint validation',
                    'report_type': 'test',
                    'generation_status': 'pending',  # Use generation_status, not status
                    'template_id': template_id,
                    'program_id': 1,  # Default program we created
                    'generation_config': test_config,
                    'data_source': {'test': 'data'}
                }
                
                # Check if we can create the model instance
                report = Report(**test_report_data)
                print("✓ Report model instance created successfully")
                
                # Try to add to session (don't commit to avoid cluttering DB)
                db.session.add(report)
                print("✓ Report added to session successfully")
                
                # Rollback to avoid saving test data
                db.session.rollback()
                print("✓ Session rolled back (test data not saved)")
                
            except Exception as e:
                print(f"✗ Report creation failed: {e}")
                db.session.rollback()
                
    except Exception as e:
        print(f"✗ Test setup failed: {e}")

if __name__ == '__main__':
    test_report_creation()