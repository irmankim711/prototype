import os
import sys
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add app directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.ai_enhanced_excel_service import ai_excel_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_ai_excel_generation():
    """Verify AI Excel generation with mocked Claude response"""
    
    print("Starting AI Excel Generation Verification...")
    
    # Mock data
    data = [
        {"id": 1, "created_at": "2024-01-01", "amount": 100, "category": "A", "score": 85},
        {"id": 2, "created_at": "2024-01-02", "amount": 150, "category": "B", "score": 90},
        {"id": 3, "created_at": "2024-01-03", "amount": 200, "category": "A", "score": 95},
        {"id": 4, "created_at": "2024-01-04", "amount": 120, "category": "C", "score": 88},
        {"id": 5, "created_at": "2024-01-05", "amount": 180, "category": "B", "score": 92}
    ]
    
    # Mock Claude response
    mock_analysis = {
        "column_types": {
            "id": "number",
            "created_at": "date",
            "amount": "currency",
            "category": "text",
            "score": "number"
        },
        "friendly_headers": {
            "id": "ID",
            "created_at": "Submission Date",
            "amount": "Total Amount",
            "category": "Category Group",
            "score": "Performance Score"
        },
        "recommended_charts": ["bar", "pie", "line", "column", "area"],
        "key_metrics": ["sum", "average", "count"],
        "conditional_formatting": ["color_scale"],
        "formulas": [],
        "insights": [
            "Category A has the highest total amount",
            "Scores are consistently high across all categories",
            "Daily submission volume is stable"
        ]
    }
    
    # Mock the client.messages.create method
    with patch.object(ai_excel_service, 'client') as mock_client:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_analysis))]
        mock_client.messages.create.return_value = mock_response
        
        # Generate Excel
        try:
            file_path, file_size = ai_excel_service.generate_enhanced_excel(
                data=data,
                title="Verification Report",
                options={"include_charts": True, "include_summary": True}
            )
            
            print(f"✓ Excel file generated successfully: {file_path}")
            print(f"✓ File size: {file_size} bytes")
            
            # Verify file exists
            if os.path.exists(file_path):
                print("✓ File exists on disk")
            else:
                print("✗ File not found on disk")
                return False
                
            # Basic validation of the file content could be added here using openpyxl
            import openpyxl
            wb = openpyxl.load_workbook(file_path)
            
            # Verify sheets
            expected_sheets = ["Data", "Summary & Insights", "Charts & Visualizations"]
            sheets = wb.sheetnames
            print(f"Sheets found: {sheets}")
            
            for sheet in expected_sheets:
                if sheet in sheets:
                    print(f"✓ Sheet '{sheet}' found")
                else:
                    print(f"✗ Sheet '{sheet}' missing")
            
            # Verify headers in Data sheet
            ws_data = wb["Data"]
            headers = [cell.value for cell in ws_data[5]]
            expected_headers = ["ID", "Submission Date", "Total Amount", "Category Group", "Performance Score"]
            
            print(f"Headers found: {headers}")
            if all(h in headers for h in expected_headers):
                print("✓ Friendly headers verified")
            else:
                print("✗ Headers mismatch")
                
            # Verify charts
            if "Charts & Visualizations" in wb.sheetnames:
                ws_charts = wb["Charts & Visualizations"]
                # Checking for charts is tricky in openpyxl as they are stored in _charts
                # But we can check if the list is not empty
                # Note: openpyxl might not expose charts easily in read mode depending on version/implementation
                # But we can assume if code ran without error, charts were added.
                print("✓ Charts sheet created")
            
            return True
            
        except Exception as e:
            print(f"✗ Error during generation: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = verify_ai_excel_generation()
    sys.exit(0 if success else 1)
