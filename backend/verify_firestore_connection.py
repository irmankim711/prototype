"""
Quick script to verify which Firestore we're connected to
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load Firebase credentials
import json
service_account_path = Path(__file__).parent / 'service' / 'report-automation-57f6e-firebase-adminsdk-fbsvc-163d1c0ed5.json'

if service_account_path.exists():
    with open(service_account_path, 'r') as f:
        service_account = json.load(f)
        project_id = service_account.get('project_id')
        client_email = service_account.get('client_email')

        print("=" * 80)
        print("LOCAL FIRESTORE CONNECTION")
        print("=" * 80)
        print(f"Project ID: {project_id}")
        print(f"Client Email: {client_email}")
        print("=" * 80)

        # Set environment variables
        os.environ['FIREBASE_PROJECT_ID'] = project_id
        os.environ['FIREBASE_CLIENT_EMAIL'] = client_email
        os.environ['FIREBASE_PRIVATE_KEY'] = service_account.get('private_key', '')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)

# Initialize Firebase
from app.middleware.firebase_auth import firebase_auth_manager

if firebase_auth_manager._initialized:
    firestore_db = firebase_auth_manager.get_firestore_db()

    # Count templates
    templates_ref = firestore_db.collection('templates')
    templates = list(templates_ref.stream())

    print(f"\nTemplates in THIS Firestore: {len(templates)}")
    print("\nTemplate List:")
    for template in templates:
        data = template.to_dict()
        print(f"  - {template.id}: {data.get('name')}")

    print("\n" + "=" * 80)
    print("This is the Firestore your LOCAL environment connects to.")
    print("Check if Railway uses the SAME project ID in its environment variables.")
    print("=" * 80)
else:
    print("❌ Failed to initialize Firebase")
