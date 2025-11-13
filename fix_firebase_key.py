"""
Firebase Private Key Formatter
This script helps format your Firebase private key correctly for Railway
"""

import json
import sys

def format_private_key_for_railway(json_file_path):
    """
    Read Firebase service account JSON and format the private key for Railway
    """
    try:
        with open(json_file_path, 'r') as f:
            service_account = json.load(f)

        print("=" * 60)
        print("FIREBASE CREDENTIALS FOR RAILWAY")
        print("=" * 60)
        print()

        # Extract values
        project_id = service_account.get('project_id')
        client_email = service_account.get('client_email')
        private_key = service_account.get('private_key')

        if not all([project_id, client_email, private_key]):
            print("❌ Error: Missing required fields in service account JSON")
            return

        print("Copy and paste these into Railway Variables:")
        print()

        # FIREBASE_PROJECT_ID
        print("1️⃣  FIREBASE_PROJECT_ID")
        print("-" * 60)
        print(project_id)
        print()

        # FIREBASE_CLIENT_EMAIL
        print("2️⃣  FIREBASE_CLIENT_EMAIL")
        print("-" * 60)
        print(client_email)
        print()

        # FIREBASE_PRIVATE_KEY - Keep the \n as literal characters
        print("3️⃣  FIREBASE_PRIVATE_KEY")
        print("-" * 60)
        print("⚠️  IMPORTANT: Copy the ENTIRE key INCLUDING the quotes!")
        print()
        print(private_key)
        print()

        print("=" * 60)
        print("✅ ALL CREDENTIALS EXTRACTED")
        print("=" * 60)
        print()
        print("📋 INSTRUCTIONS:")
        print("1. Go to Railway → Your Backend Project → Variables")
        print("2. For each variable above:")
        print("   - Click 'New Variable' or edit existing")
        print("   - Paste the EXACT value shown (including \\n characters)")
        print("3. Save and wait for Railway to redeploy")
        print()

        # Additional debug info
        print("🔍 DEBUG INFO:")
        print(f"   Private key length: {len(private_key)} characters")
        print(f"   Starts with: {private_key[:30]}...")
        print(f"   Contains \\n: {'Yes' if '\\n' in private_key else 'No'}")
        print(f"   Has BEGIN marker: {'Yes' if 'BEGIN PRIVATE KEY' in private_key else 'No'}")
        print()

    except FileNotFoundError:
        print(f"❌ Error: File not found: {json_file_path}")
        print()
        print("Usage: python fix_firebase_key.py path/to/serviceAccount.json")
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON file: {json_file_path}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Firebase Private Key Formatter for Railway")
        print("=" * 60)
        print()
        print("Usage:")
        print("  python fix_firebase_key.py <path-to-service-account.json>")
        print()
        print("Example:")
        print("  python fix_firebase_key.py C:\\Downloads\\serviceAccount.json")
        print()
        print("This will extract and properly format your Firebase credentials")
        print("for Railway environment variables.")
        print()
        sys.exit(1)

    json_file_path = sys.argv[1]
    format_private_key_for_railway(json_file_path)
