#!/usr/bin/env python
"""
Test Google Forms OAuth Flow
Creates a test session and initiates OAuth flow
"""

import requests
import webbrowser

BASE_URL = "http://localhost:5000"

# Create a session with a test user_id
session = requests.Session()

# Set a cookie to simulate logged-in user (user_id=1)
session.cookies.set('user_id', '1', domain='localhost')

print("📋 Testing Google Forms OAuth Flow")
print("=" * 60)

# Step 1: Check status
print("\n1️⃣  Checking Google Forms status...")
response = session.get(f"{BASE_URL}/api/google-forms/status")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

# Step 2: Initiate OAuth
print("\n2️⃣  Initiating Google OAuth...")
response = session.post(f"{BASE_URL}/api/google-forms/oauth/authorize")
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success')}")

    auth_url = data.get('authorization_url')
    if auth_url:
        print(f"\n✅ Authorization URL generated!")
        print(f"🔗 {auth_url}")
        print(f"\n📱 Opening browser...")
        webbrowser.open(auth_url)
        print("\n✅ Complete the authorization in your browser")
        print("   After authorizing, you'll be redirected back to the app")
    else:
        print("❌ No authorization URL returned")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "=" * 60)
