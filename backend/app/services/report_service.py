from ..models import Report#, ReportTemplate
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from reportlab.pdfgen import canvas
import json
import os

class ReportService:
    def __init__(self):
        self.credentials = None
        self.initialize_google_credentials()

    def initialize_google_credentials(self):
        # Initialize Google credentials from environment variables
        token_info = os.getenv("GOOGLE_TOKEN_INFO")
        if token_info:
            self.credentials = Credentials.from_authorized_user_info(json.loads(token_info))

    def get_templates(self):
        # templates = ReportTemplate.query.filter_by(is_active=True).all()
        # return [{'id': t.id, 'name': t.name, 'description': t.description} for t in templates]
        return []

    def generate_report(self, template_id, data):
        # template = ReportTemplate.query.get(template_id)
        # if not template:
        #     raise ValueError("Template not found")

        # # Generate PDF report
        output_path = f"reports/report_{template_id}_{data.get('id')}.pdf"
        # self.generate_pdf(template, data, output_path)

        # # If template is linked to Google Sheets, update the sheet
        # if data.get('update_sheet'):
        #     self.update_google_sheet(data)

        return output_path

    def generate_pdf(self, template, data, output_path):
        c = canvas.Canvas(output_path)
        # Add PDF generation logic here based on template and data
        c.drawString(100, 750, f"Report: {template.name}")
        c.save()

    def update_google_sheet(self, data):
        if not self.credentials:
            raise ValueError("Google credentials not initialized")

        service = build('sheets', 'v4', credentials=self.credentials)
        spreadsheet_id = data.get('spreadsheet_id')
        range_name = data.get('range_name', 'Sheet1!A1')
        
        values = [[data.get('value1'), data.get('value2')]]
        body = {'values': values}
        
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

report_service = ReportService()
