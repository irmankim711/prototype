"""
Check exact Firestore template configuration
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load Firebase credentials
service_account_path = Path(__file__).parent / 'service' / 'report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json'

if service_account_path.exists():
    with open(service_account_path, 'r') as f:
        service_account = json.load(f)
        os.environ['FIREBASE_PROJECT_ID'] = service_account.get('project_id')
        os.environ['FIREBASE_CLIENT_EMAIL'] = service_account.get('client_email')
        os.environ['FIREBASE_PRIVATE_KEY'] = service_account.get('private_key', '')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)

# Initialize Firebase
from app.middleware.firebase_auth import firebase_auth_manager

if firebase_auth_manager._initialized:
    firestore_db = firebase_auth_manager.get_firestore_db()

    # Get the template details
    template_ref = firestore_db.collection('templates').document('uwais_global_solution')
    doc = template_ref.get()

    if doc.exists:
        data = doc.to_dict()
        print("=" * 80)
        print("FIRESTORE TEMPLATE CONFIGURATION")
        print("=" * 80)
        print(f"Document ID: {doc.id}")
        print(f"Name: {data.get('name')}")
        print(f"File Name: {data.get('file_name')}")
        print(f"File Path: {data.get('file_path')}")
        print(f"Absolute Path: {data.get('absolute_path')}")
        print(f"Active: {data.get('is_active')}")
        print(f"Supports Loops: {data.get('supports_loops')}")
        print(f"Version: {data.get('version')}")
        print("=" * 80)

        # Check if the file exists locally
        file_name = data.get('file_name')
        if file_name:
            templates_dir = Path(__file__).parent / 'templates'
            local_path = templates_dir / file_name

            print(f"\nLocal File Check:")
            print(f"  Expected path: {local_path}")
            print(f"  File exists: {local_path.exists()}")
            if local_path.exists():
                print(f"  File size: {local_path.stat().st_size} bytes")

        print("\n" + "=" * 80)
        print("THIS IS THE FILE RAILWAY WILL USE")
        print("=" * 80)
        print(f"Railway will look for: /app/templates/{file_name}")
        print(f"\nMake sure '{file_name}' is the correct template!")
    else:
        print("❌ Template not found in Firestore")
else:
    print("❌ Firebase not initialized")
