"""
Debug script to diagnose why Google Forms responses are returning 0
"""
import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.google_forms_service import google_forms_service
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_form_responses(user_id: str, form_id: str):
    """Debug form responses fetching"""

    print("\n" + "="*60)
    print("GOOGLE FORMS RESPONSES DEBUG")
    print("="*60)

    # Check if service is enabled
    if google_forms_service is None:
        print(f"\n1. Service Status: ❌ Disabled (service is None)")
        print("   ERROR: Google Forms service is not enabled")
        print("   Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        return

    print(f"\n1. Service Status: {'✅ Enabled' if google_forms_service.is_enabled() else '❌ Disabled'}")

    if not google_forms_service.is_enabled():
        print("   ERROR: Google Forms service is not enabled")
        print("   Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        return

    # Check credentials
    print(f"\n2. Checking credentials for user {user_id}...")
    credentials = google_forms_service._get_user_credentials(user_id)

    if not credentials:
        print(f"   ❌ No credentials found for user {user_id}")
        print(f"   User needs to authorize via OAuth")
        return

    print(f"   ✅ Credentials found")
    print(f"   Token valid: {not credentials.expired if credentials.expiry else 'Unknown'}")
    print(f"   Scopes: {credentials.scopes}")

    # Try to fetch form structure
    print(f"\n3. Fetching form structure for {form_id}...")
    try:
        from googleapiclient.discovery import build
        forms_service = build('forms', 'v1', credentials=credentials)

        form = forms_service.forms().get(formId=form_id).execute()
        print(f"   ✅ Form found: {form.get('info', {}).get('title', 'Unknown')}")
        print(f"   Questions: {len(form.get('items', []))}")
        print(f"   Published URL: {form.get('responderUri', 'Not set')}")
        print(f"   Settings: {json.dumps(form.get('settings', {}), indent=2)}")

    except Exception as e:
        print(f"   ❌ Error fetching form: {e}")
        return

    # Try to fetch responses - RAW API call
    print(f"\n4. Fetching responses (RAW API call)...")
    try:
        responses_result = forms_service.forms().responses().list(
            formId=form_id
        ).execute()

        print(f"   API Response Keys: {list(responses_result.keys())}")
        print(f"   Raw Response: {json.dumps(responses_result, indent=2)}")

        responses = responses_result.get('responses', [])
        print(f"\n   Total Responses: {len(responses)}")

        if len(responses) == 0:
            print("\n   ⚠️  DIAGNOSIS: Form has 0 responses")
            print("   Possible reasons:")
            print("   1. No one has filled out the form yet")
            print("   2. Form is not accepting responses (check settings)")
            print("   3. Responses are being collected in a linked Google Sheet")
            print("   4. OAuth scope issue - need 'forms.responses.readonly' scope")
            print(f"\n   Action: Submit a test response at: {form.get('responderUri', 'URL not available')}")
        else:
            print(f"\n   ✅ Found {len(responses)} responses!")
            print(f"\n   First response sample:")
            print(json.dumps(responses[0], indent=2))

    except Exception as e:
        print(f"   ❌ Error fetching responses: {e}")
        import traceback
        traceback.print_exc()

    # Check if form is linked to a Sheet
    print(f"\n5. Checking for linked Google Sheet...")
    try:
        drive_service = build('drive', 'v3', credentials=credentials)

        # Check if form has a linked sheet
        if 'linkedSheetId' in form.get('info', {}):
            sheet_id = form['info']['linkedSheetId']
            print(f"   ✅ Form is linked to Google Sheet: {sheet_id}")
            print(f"   Note: Responses might be in the Sheet instead")
        else:
            print(f"   ℹ️  No linked Google Sheet found")

    except Exception as e:
        print(f"   ⚠️  Could not check for linked sheet: {e}")

    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_google_forms_responses.py <user_id> <form_id>")
        print("\nExample:")
        print("  python debug_google_forms_responses.py user123 1FAIpQLSe_xxxxxxxxxxxx")
        sys.exit(1)

    user_id = sys.argv[1]
    form_id = sys.argv[2]

    debug_form_responses(user_id, form_id)
