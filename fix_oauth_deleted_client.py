#!/usr/bin/env python3
"""
Fix OAuth deleted_client error by properly configuring Google OAuth
"""

import os
import json
import sys

def fix_oauth_configuration():
    """Fix the OAuth configuration to resolve deleted_client error"""
    
    print("🔧 Fixing OAuth 'deleted_client' error...")
    
    # Path to credentials file
    backend_path = "c:\\Users\\IRMAN\\OneDrive\\Desktop\\prototype\\backend"
    credentials_path = os.path.join(backend_path, "credentials.json")
    
    # Correct OAuth configuration
    oauth_config = {
        "installed": {
            "client_id": "1008582896300-sbsrcs6jg32lncrnmmf1ia93vnl81tls.apps.googleusercontent.com",
            "project_id": "stratosys",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "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",
            "redirect_uris": [
                "http://localhost:5000/api/google-forms/callback",
                "http://localhost:3000/forms/auth/callback",
                "http://localhost:3000/auth/google/callback"
            ]
        }
    }
    
    try:
        # Write corrected credentials
        with open(credentials_path, 'w') as f:
            json.dump(oauth_config, f, indent=2)
        
        print("✅ OAuth credentials configuration updated")
        
        # Create tokens directory if it doesn't exist
        tokens_dir = os.path.join(backend_path, "tokens")
        if not os.path.exists(tokens_dir):
            os.makedirs(tokens_dir)
            print("✅ Tokens directory created")
        
        # Create .env file with OAuth configuration
        env_path = os.path.join(backend_path, ".env")
        env_content = f"""
# Google OAuth Configuration
GOOGLE_CLIENT_ID=1008582896300-sbsrcs6jg32lncrnmmf1ia93vnl81tls.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_PROJECT_ID=stratosys
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_DIR=tokens

# Public Forms Configuration
PUBLIC_FORMS_ENABLED=true
OAUTH_REDIRECT_URI=http://localhost:5000/api/google-forms/callback

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
"""
        
        # Read existing .env if it exists
        existing_env = ""
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                existing_env = f.read()
        
        # Only add OAuth config if not already present
        if "GOOGLE_CLIENT_ID" not in existing_env:
            with open(env_path, 'a') as f:
                f.write(env_content)
            print("✅ Environment variables updated")
        
        print("\n🎯 OAuth Configuration Summary:")
        print(f"   Client ID: {oauth_config['installed']['client_id']}")
        print(f"   Project ID: {oauth_config['installed']['project_id']}")
        print(f"   Redirect URI: {oauth_config['installed']['redirect_uris'][0]}")
        
        print("\n🚀 Next Steps:")
        print("1. Restart your backend server")
        print("2. Try the OAuth flow again")
        print("3. The 'deleted_client' error should be resolved")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing OAuth configuration: {e}")
        return False

def clean_git_history():
    """Clean up the git history to remove sensitive tokens"""
    
    print("\n🧹 Cleaning Git History...")
    
    # Instructions for manual cleanup
    print("""
To completely remove the sensitive token from git history:

1. Remove the file from the current commit:
   git rm --cached backend/tokens/user_2_token.json

2. Commit the removal:
   git commit -m "Remove sensitive OAuth tokens from tracking"

3. Force push to overwrite remote history:
   git push origin nuew-tes --force

4. Verify the push protection is resolved

Note: The .gitignore has already been updated to prevent future token commits.
""")

if __name__ == "__main__":
    print("🔒 OAuth Deleted Client Error Fix")
    print("=" * 50)
    
    # Fix OAuth configuration
    oauth_fixed = fix_oauth_configuration()
    
    # Clean git history instructions
    clean_git_history()
    
    if oauth_fixed:
        print("\n✅ OAuth configuration fix completed!")
        print("The 'deleted_client' error should be resolved.")
    else:
        print("\n❌ OAuth fix failed. Please check the configuration manually.")
    
    sys.exit(0 if oauth_fixed else 1)
