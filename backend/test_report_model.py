#!/usr/bin/env python3
"""
Test script to check the Report model import and constructor
"""

from app import create_app, db
from app.models import Report

def test_report_model():
    """Test the Report model to see what it accepts"""
    
    app = create_app()
    with app.app_context():
        print("🔍 Testing Report model...")
        
        # Check the Report class
        print(f"📋 Report class: {Report}")
        print(f"📋 Report module: {Report.__module__}")
        print(f"📋 Report file: {Report.__file__ if hasattr(Report, '__file__') else 'No __file__'}")
        
        # Check the constructor
        print(f"📋 Report __init__: {Report.__init__}")
        
        # Try to create a Report instance with minimal data
        try:
            report = Report(
                title="Test Report",
                user_id=1
            )
            print("✅ Successfully created Report instance")
            print(f"📋 Report instance: {report}")
            print(f"📋 Report user_id: {report.user_id}")
        except Exception as e:
            print(f"❌ Failed to create Report instance: {e}")
            print(f"📋 Error type: {type(e)}")
            
            # Check what parameters the constructor accepts
            import inspect
            try:
                sig = inspect.signature(Report.__init__)
                print(f"📋 Constructor signature: {sig}")
                print(f"📋 Constructor parameters: {list(sig.parameters.keys())}")
            except Exception as sig_e:
                print(f"❌ Could not inspect constructor: {sig_e}")

if __name__ == "__main__":
    test_report_model()
