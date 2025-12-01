import sys
import os
from pathlib import Path
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.production.report_models import Report

app = create_app()

def test_report_attributes():
    with app.app_context():
        print("Creating a test Report object...")
        report = Report(
            title="Test Report",
            file_path="/tmp/test.docx",
            file_format="docx"
        )
        
        print(f"Report created: {report}")
        print(f"File path: {report.file_path}")
        print(f"File format: {report.file_format}")
        
        try:
            print(f"Accessing docx_file_path: {report.docx_file_path}")
        except AttributeError as e:
            print(f"❌ AttributeError caught: {e}")
            
        try:
            print(f"Accessing pdf_file_path: {report.pdf_file_path}")
        except AttributeError as e:
            print(f"❌ AttributeError caught: {e}")

if __name__ == "__main__":
    test_report_attributes()
