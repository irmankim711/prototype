"""
Example API Integration Usage
Run this script to test the Google Sheets integration
"""

import asyncio
from app.services.google_sheets_service import google_sheets_service

async def test_integration():
    """Test the API integration setup"""
    try:
        # Test Google Sheets service initialization
        metrics = google_sheets_service.get_metrics()
        print(f"Google Sheets service initialized: {metrics}")
        
        # Add more tests here
        print("✓ API Integration setup is working!")
        
    except Exception as e:
        print(f"✗ Setup test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())
