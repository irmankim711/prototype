"""Check report details"""
import sys
sys.path.insert(0, r'c:\Users\IRMAN\OneDrive\Desktop\prototype\backend')

from app import create_app, db
from app.models import Report
import os

app = create_app()
with app.app_context():
    report = Report.query.get(96)
    if report:
        print(f"Report {report.id}:")
        print(f"  Title: {report.title}")
        print(f"  Status: {report.status}")
        print(f"  File path: {report.file_path}")
        print(f"  PDF file path: {report.pdf_file_path if hasattr(report, 'pdf_file_path') else 'N/A'}")
        print(f"  Excel file path: {report.excel_file_path if hasattr(report, 'excel_file_path') else 'N/A'}")

        if report.file_path:
            print(f"  DOCX exists: {os.path.exists(report.file_path)}")
            if os.path.exists(report.file_path):
                print(f"  DOCX size: {os.path.getsize(report.file_path)} bytes")

        if hasattr(report, 'pdf_file_path') and report.pdf_file_path:
            print(f"  PDF exists: {os.path.exists(report.pdf_file_path)}")
            if os.path.exists(report.pdf_file_path):
                print(f"  PDF size: {os.path.getsize(report.pdf_file_path)} bytes")
    else:
        print("Report 96 not found")
