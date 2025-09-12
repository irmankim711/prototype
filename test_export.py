#!/usr/bin/env python3
"""
Quick test of the unified export endpoint
"""
import requests
import json

def test_export():
    url = "http://127.0.0.1:5000/api/reports/export"
    data = {
        "template_id": "test",
        "data_source": {"title": "Test Report", "summary": "This is a test"},
        "formats": ["html"]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Export URLs: {result.get('urls', {})}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_export()
