#!/usr/bin/env python3
"""
Simple test to verify our new submissions endpoint works
"""

import requests
import json

# Test the authentication endpoint first
def test_login():
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {
        "email": "test@test.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_submissions_endpoint():
    token = test_login()
    if not token:
        print("Could not get authentication token")
        return
    
    # Test the new submissions endpoint
    submissions_url = "http://localhost:5000/api/forms/submissions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(submissions_url, headers=headers)
        print(f"Submissions endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('submissions', []))} submissions")
            print(f"Pagination: {data.get('pagination', {})}")
            
            # Print first submission as example
            submissions = data.get('submissions', [])
            if submissions:
                print(f"First submission example:")
                first_sub = submissions[0]
                print(f"  Name: {first_sub.get('name', 'N/A')}")
                print(f"  Email: {first_sub.get('email', 'N/A')}")
                print(f"  Score: {first_sub.get('score', 'N/A')}")
                print(f"  Form: {first_sub.get('form_title', 'N/A')}")
                print(f"  Date: {first_sub.get('date', 'N/A')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_submissions_endpoint()
