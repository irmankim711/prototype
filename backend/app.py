from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd

app = Flask(__name__)
CORS(app)

# --- Google Sheets API Integration ---
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Set these to your Google Sheet details
SHEET_ID = 'YOUR_SHEET_ID_HERE'  # <-- Replace with your Sheet ID
SHEET_RANGE = 'Sheet1!A1:Z1000'  # <-- Adjust as needed

# Path to your credentials file
GOOGLE_CREDS_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')

# --- AI Integration Placeholders ---
# Placeholder: OpenAI/ChatGPT and Llama integration will be added here

@app.route('/fetch-data', methods=['GET'])
def fetch_data():
    try:
        # Authenticate and build the Sheets API client
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=[
            'https://www.googleapis.com/auth/spreadsheets.readonly'])
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE).execute()
        values = result.get('values', [])
        if not values:
            return jsonify({'data': [], 'message': 'No data found.'})
        # First row is header
        headers = values[0]
        data = [dict(zip(headers, row)) for row in values[1:]]
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-report', methods=['POST'])
def generate_report():
    # TODO: Implement report generation/export
    df = pd.DataFrame(request.json['data'])
    output_path = 'report.xlsx'
    df.to_excel(output_path, index=False)
    return send_file(output_path, as_attachment=True)

@app.route('/suggest-template', methods=['POST'])
def suggest_template():
    # TODO: Integrate ChatGPT/Llama for template suggestion
    prompt = request.json.get('prompt', '')
    # Return mock templates for now
    templates = [
        'Summary Report Template',
        'Detailed Analysis Template',
        'Custom Template based on: ' + prompt
    ]
    return jsonify({'templates': templates})

if __name__ == '__main__':
    app.run(debug=True)
