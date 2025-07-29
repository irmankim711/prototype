#!/usr/bin/env python3
"""
Test Excel optimization functionality
"""
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_excel_optimization():
    """Test the Excel template optimization endpoint"""
    
    # Use the test Excel file directly
    excel_file = "test_simple.xlsx"
    logger.info(f"Using Excel file: {excel_file}")
    
    # Test the Excel optimization endpoint
    url = f"http://127.0.0.1:5000/api/mvp/ai/optimize-template-with-excel"
    
    payload = {
        "template_name": "Temp2.tex",
        "excel_file": excel_file
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Testing Excel optimization URL: {url}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        logger.info(f"Response status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            logger.info(f"Response JSON: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and result.get('success'):
                logger.info("Excel optimization successful!")
                return True
            else:
                logger.error(f"Excel optimization failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            logger.error(f"Unexpected response format: {response.text[:200]}")
            return False
            
    except Exception as e:
        logger.error(f"Excel optimization test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing Excel optimization...")
    success = test_excel_optimization()
    logger.info(f"Excel optimization test result: {'PASS' if success else 'FAIL'}")
