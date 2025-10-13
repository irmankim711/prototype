#!/usr/bin/env python3
"""
Quick login debug script to test what's happening with authentication
"""
import requests
import json

def test_backend_endpoints():
    """Test which backend endpoints are available"""
    base_url = "http://localhost:5000"

    print("🔍 Testing backend endpoints...")

    # Test root
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Root endpoint error: {e}")

    # Test auth endpoints
    auth_endpoints = [
        "/auth/firebase-sync",
        "/auth/profile",
        "/auth/firebase-health",
        "/api/auth/firebase-sync",
        "/api/auth/profile"
    ]

    for endpoint in auth_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"{endpoint}: {response.status_code}")
            if response.status_code != 404:
                try:
                    print(f"  Response: {response.json()}")
                except:
                    print(f"  Response: {response.text[:100]}")
        except Exception as e:
            print(f"{endpoint} error: {e}")

def test_firebase_token():
    """Test if we can create a dummy Firebase token request"""
    print("\n🔥 Testing Firebase token simulation...")

    # Simulate what the frontend sends
    dummy_payload = {
        "firstName": "Test",
        "lastName": "User",
        "displayName": "Test User",
        "photoUrl": None,
        "emailVerified": True
    }

    headers = {
        "Authorization": "Bearer dummy-firebase-token",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "http://localhost:5000/auth/firebase-sync",
            json=dummy_payload,
            headers=headers
        )
        print(f"Firebase sync test: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Firebase sync error: {e}")

def check_database_connection():
    """Check if we can connect to the database"""
    print("\n📊 Testing database connection...")

    try:
        response = requests.get("http://localhost:5000/users")
        print(f"Users endpoint: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users in database")
    except Exception as e:
        print(f"Database test error: {e}")

if __name__ == "__main__":
    print("🚀 Starting login debug tests...\n")

    test_backend_endpoints()
    test_firebase_token()
    check_database_connection()

    print("\n✅ Debug tests complete!")