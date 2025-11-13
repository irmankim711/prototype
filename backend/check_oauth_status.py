"""
Quick check to see if OAuth token was created
"""
import os
from pathlib import Path

user_id = 'SOejiqo9O4MNBYKly19rHaDt9et1'
token_path = Path('backend/tokens') / f'user_{user_id}_google_token.json'

print("\n" + "="*60)
if token_path.exists():
    print("✅ SUCCESS! OAuth token has been created!")
    print(f"Token file: {token_path}")
    print("\nYou can now fetch Google Forms responses.")
    print("\nNext step: Try calling the API endpoint:")
    print(f"GET /api/google-forms/forms/1yxEBr9GZ8hFB0hWCVFiMJPc8YyferneZeX7_JwHlRus/responses")
else:
    print("❌ OAuth token NOT created yet")
    print(f"Expected file: {token_path}")
    print("\nPlease complete the OAuth flow:")
    print("1. Go to /google-forms-export")
    print("2. Click 'Sign in with Google'")
    print("3. Use account: firebts5k@gmail.com")
    print("4. Allow all permissions")
    print("5. Wait for popup to close")
    print("6. Run this script again")
print("="*60 + "\n")
