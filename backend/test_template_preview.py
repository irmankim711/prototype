#!/usr/bin/env python3
"""
Test script to debug template preview functionality
"""
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_template_preview():
    """Test the template preview endpoint"""
    
    url = "http://127.0.0.1:5000/api/mvp/templates/Temp2.tex/preview"
    
    # Test data
    test_data = {
        "data": {
            "title": "Test Project",
            "general_description": "This is a test description",
            "program": {
                "title": "Sample Program",
                "date": "2025-01-20",
                "location": "Test Location"
            },
            "tentative": {
                "day1": [
                    {
                        "time": "9:00 AM",
                        "activity": "Opening Ceremony",
                        "description": "Welcome remarks",
                        "handler": "John Doe"
                    }
                ],
                "day2": [
                    {
                        "time": "9:00 AM", 
                        "activity": "Closing",
                        "description": "Summary and closing",
                        "handler": "Jane Smith"
                    }
                ]
            },
            "participants": [
                {
                    "name": "Alice Johnson",
                    "organization": "Company A",
                    "position": "Manager"
                },
                {
                    "name": "Bob Smith", 
                    "organization": "Company B",
                    "position": "Director"
                }
            ]
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Testing URL: {url}")
        logger.info(f"Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(url, json=test_data, headers=headers)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            logger.info(f"Response JSON: {json.dumps(result, indent=2)}")
        else:
            logger.info(f"Response text: {response.text[:500]}...")
            
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

def test_placeholders():
    """Test the placeholders endpoint"""
    
    url = "http://127.0.0.1:5000/api/mvp/templates/Temp2.tex/placeholders"
    
    try:
        logger.info(f"Testing placeholders URL: {url}")
        
        response = requests.get(url)
        
        logger.info(f"Placeholders response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Placeholders found: {len(result.get('placeholders', []))}")
            return True
        else:
            logger.error(f"Placeholders test failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Placeholders test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting template tests...")
    
    # Test placeholders first
    logger.info("=== Testing Placeholders ===")
    placeholders_ok = test_placeholders()
    
    # Test preview
    logger.info("=== Testing Preview ===")
    preview_ok = test_template_preview()
    
    logger.info(f"Results: Placeholders: {placeholders_ok}, Preview: {preview_ok}")
