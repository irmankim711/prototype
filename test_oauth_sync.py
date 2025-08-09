#!/usr/bin/env python3
"""
Quick OAuth Configuration Test
"""

import os
import re
from pathlib import Path

def check_oauth_config():
    print("🔍 OAuth Configuration Verification")
    print("=" * 40)
    
    # Expected client ID (NEW working one)
    expected_client_id = "1008582896300-sbsrcs6jg32lncrnmmf1ia93vnl81tls.apps.googleusercontent.com"
    
    # Files to check
    files_to_check = [
        ("Backend .env", "backend/.env", [
            r'GOOGLE_CLIENT_ID=(.+)',
            r'client_id=(.+)'
        ]),
        ("Frontend .env.local", "frontend/.env.local", [
            r'VITE_GOOGLE_CLIENT_ID=(.+)'
        ]),
        ("Frontend .env", "frontend/.env", [
            r'VITE_GOOGLE_CLIENT_ID=(.+)'
        ]),
        ("Frontend index.html", "frontend/index.html", [
            r'data-client_id="([^"]+)"'
        ])
    ]
    
    all_good = True
    
    for file_desc, file_path, patterns in files_to_check:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ {file_desc}: File not found - {file_path}")
            continue
            
        with open(path, 'r') as f:
            content = f.read()
        
        found_any = False
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                found_any = True
                if match.strip() == expected_client_id:
                    print(f"✅ {file_desc}: Correct client ID")
                else:
                    print(f"❌ {file_desc}: Wrong client ID - {match[:50]}...")
                    all_good = False
        
        if not found_any:
            print(f"⚠️  {file_desc}: No client ID found")
    
    print("\n" + "=" * 40)
    if all_good:
        print("🎉 All configurations are synchronized!")
        print("🚀 Ready to test OAuth!")
    else:
        print("❌ Configuration issues found. Please fix them first.")
    
    return all_good

if __name__ == "__main__":
    check_oauth_config()
