#!/usr/bin/env python3
"""
Test script for the new template endpoints
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))

def test_list_templates():
    """Test the template list endpoint"""
    print("Testing template list endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/mvp/templates/list")
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Found {len(templates)} templates:")
            for template in templates:
                print(f"  - {template['name']} ({template['filename']})")
            return templates
        else:
            print(f"❌ Failed to get templates: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting templates: {e}")
        return []

def test_template_placeholders(template_name):
    """Test the placeholders endpoint"""
    print(f"\nTesting placeholders for template: {template_name}")
    try:
        response = requests.get(f"{BASE_URL}/mvp/templates/{template_name}/placeholders")
        if response.status_code == 200:
            data = response.json()
            placeholders = data.get('placeholders', [])
            print(f"✅ Found {len(placeholders)} placeholders:")
            for placeholder in placeholders:
                print(f"  - {placeholder}")
            return placeholders
        else:
            print(f"❌ Failed to get placeholders: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting placeholders: {e}")
        return []

def test_template_content(template_name):
    """Test the content extraction endpoint"""
    print(f"\nTesting content extraction for template: {template_name}")
    try:
        response = requests.get(f"{BASE_URL}/mvp/templates/{template_name}/content")
        if response.status_code == 200:
            data = response.json()
            content = data.get('content', [])
            placeholders = data.get('placeholders', [])
            print(f"✅ Extracted {len(content)} content items and {len(placeholders)} placeholders")
            return data
        else:
            print(f"❌ Failed to get content: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting content: {e}")
        return None

def test_live_preview(template_name, test_data):
    """Test the live preview endpoint"""
    print(f"\nTesting live preview for template: {template_name}")
    try:
        response = requests.post(
            f"{BASE_URL}/mvp/templates/{template_name}/preview",
            json={"data": test_data},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            preview_url = data.get('preview')
            filename = data.get('filename')
            print(f"✅ Generated preview: {filename}")
            print(f"   Preview URL: {preview_url[:50]}...")
            return data
        else:
            print(f"❌ Failed to generate preview: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error generating preview: {e}")
        return None

def main():
    """Run all tests"""
    print("🧪 Testing Template Endpoints")
    print("=" * 50)
    
    # Test 1: List templates
    templates = test_list_templates()
    
    if not templates:
        print("\n❌ No templates found. Please ensure you have .docx files in the templates directory.")
        return
    
    # Test 2: Get placeholders for first template
    first_template = templates[0]['filename']
    placeholders = test_template_placeholders(first_template)
    
    # Test 3: Get content for first template
    content_data = test_template_content(first_template)
    
    # Test 4: Generate live preview
    if placeholders:
        # Create test data based on placeholders
        test_data = {}
        for placeholder in placeholders:
            test_data[placeholder] = f"Test value for {placeholder}"
        
        preview_data = test_live_preview(first_template, test_data)
    
    print("\n" + "=" * 50)
    print("✅ Template endpoint tests completed!")
    print("\nTo test the frontend:")
    print("1. Start the backend: python run.py")
    print("2. Start the frontend: cd ../frontend && npm run dev")
    print("3. Navigate to the report builder and test the new features")

if __name__ == "__main__":
    main() 