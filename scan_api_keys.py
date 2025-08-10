#!/usr/bin/env python3
"""
API Key Scanner and Cleaner
Scans the codebase for potential API keys and helps clean them up
"""

import re
import os
import sys
from pathlib import Path

# Patterns for different types of API keys and secrets
PATTERNS = {
    'google_api_key': r'AIzaSy[A-Za-z0-9_-]{33}',
    'google_client_secret': r'GOCSPX-[A-Za-z0-9_-]+',
    'openai_key': r'sk-[A-Za-z0-9]{48}',
    'slack_token': r'xox[bpoa]-[A-Za-z0-9-]+',
    'github_token': r'github_pat_[A-Za-z0-9_]{82}',
    'generic_api_key': r'api[_-]?key["\'\s]*[:=]["\'\s]*[A-Za-z0-9_-]{20,}',
    'generic_secret': r'secret[_-]?key["\'\s]*[:=]["\'\s]*[A-Za-z0-9_-]{20,}',
    'generic_token': r'access[_-]?token["\'\s]*[:=]["\'\s]*[A-Za-z0-9_-]{20,}',
}

# Files and directories to exclude from scanning
EXCLUDE_PATTERNS = [
    r'\.git',
    r'node_modules',
    r'__pycache__',
    r'\.venv',
    r'venv',
    r'\.pytest_cache',
    r'dist',
    r'build',
    r'\.egg-info',
    r'\.template$',
    r'SECURITY_API_KEYS\.md',
    r'setup-env\.',
]

# File extensions to scan
SCAN_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yml', '.yaml', '.env', '.config', '.conf'}

def should_exclude(path):
    """Check if a path should be excluded from scanning"""
    path_str = str(path)
    return any(re.search(pattern, path_str) for pattern in EXCLUDE_PATTERNS)

def scan_file(file_path):
    """Scan a single file for API keys and secrets"""
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for pattern_name, pattern in PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Get line number
                line_num = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_num - 1].strip()
                
                findings.append({
                    'file': file_path,
                    'line': line_num,
                    'pattern': pattern_name,
                    'match': match.group(),
                    'line_content': line_content
                })
                
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return findings

def scan_directory(directory):
    """Scan all files in a directory recursively"""
    all_findings = []
    
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from dirs list to prevent walking into them
        dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip excluded files and non-text files
            if should_exclude(file_path) or file_path.suffix not in SCAN_EXTENSIONS:
                continue
                
            findings = scan_file(file_path)
            all_findings.extend(findings)
    
    return all_findings

def main():
    print("🔍 API Key Scanner - Searching for potential API keys and secrets...")
    print("=" * 70)
    
    # Get the project root directory
    project_root = Path.cwd()
    
    # Scan the project
    findings = scan_directory(project_root)
    
    if not findings:
        print("✅ No API keys or secrets found in the codebase!")
        return 0
    
    # Group findings by file
    files_with_issues = {}
    for finding in findings:
        file_path = finding['file']
        if file_path not in files_with_issues:
            files_with_issues[file_path] = []
        files_with_issues[file_path].append(finding)
    
    print(f"🚨 Found {len(findings)} potential API keys/secrets in {len(files_with_issues)} files:")
    print()
    
    for file_path, file_findings in files_with_issues.items():
        print(f"📄 {file_path}")
        for finding in file_findings:
            print(f"   Line {finding['line']}: {finding['pattern']}")
            print(f"   Content: {finding['line_content']}")
            print(f"   Match: {finding['match']}")
            print()
    
    print("🔧 Recommended Actions:")
    print("1. Move sensitive values to .env files")
    print("2. Use template files with placeholder values")
    print("3. Ensure .env files are in .gitignore")
    print("4. Revoke and regenerate any exposed API keys")
    print("5. Use environment variables in production")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
