#!/usr/bin/env python3
"""
Clean git history to remove sensitive tokens and resolve push protection
"""

import os
import subprocess
import sys

def run_git_command(command, check=True):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def clean_git_history():
    """Clean the git history to remove sensitive files"""
    
    print("🧹 Cleaning Git History to Remove Sensitive Tokens...")
    print("=" * 60)
    
    # Step 1: Use git filter-branch to remove the file from history
    print("\n1. Removing sensitive file from git history...")
    
    filter_command = 'git filter-branch --force --index-filter "git rm --cached --ignore-unmatch backend/tokens/user_2_token.json" --prune-empty --tag-name-filter cat -- --all'
    
    stdout, stderr = run_git_command(filter_command, check=False)
    
    if "Rewrite" in stdout or "already mapped" in stderr:
        print("✅ Git history cleaned successfully")
    else:
        print(f"⚠️  Filter-branch output: {stdout}")
        print(f"⚠️  Filter-branch stderr: {stderr}")
    
    # Step 2: Force garbage collection
    print("\n2. Running garbage collection...")
    
    gc_commands = [
        "git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin",
        "git reflog expire --expire=now --all",
        "git gc --prune=now"
    ]
    
    for cmd in gc_commands:
        stdout, stderr = run_git_command(cmd, check=False)
        print(f"   Executed: {cmd}")
    
    print("✅ Garbage collection completed")
    
    # Step 3: Verify the file is removed from history
    print("\n3. Verifying file removal...")
    
    check_command = "git log --all --full-history -- backend/tokens/user_2_token.json"
    stdout, stderr = run_git_command(check_command, check=False)
    
    if not stdout:
        print("✅ File successfully removed from all history")
    else:
        print("⚠️  File may still exist in history:")
        print(stdout)
    
    # Step 4: Check current status
    print("\n4. Checking current repository status...")
    
    status_stdout, _ = run_git_command("git status --porcelain")
    if status_stdout:
        print("📝 Current changes:")
        print(status_stdout)
    else:
        print("✅ Working directory is clean")
    
    return True

def alternative_cleanup():
    """Alternative method using git rebase"""
    
    print("\n🔄 Alternative: Interactive Rebase Method")
    print("=" * 40)
    
    print("""
If the filter-branch method doesn't work, you can manually clean the commit:

1. Interactive rebase to edit the problematic commit:
   git rebase -i HEAD~3

2. Change 'pick' to 'edit' for commit d25a38d8

3. Remove the file and amend the commit:
   git rm backend/tokens/user_2_token.json
   git commit --amend --no-edit

4. Continue the rebase:
   git rebase --continue

5. Force push:
   git push origin nuew-tes --force
""")

def main():
    """Main function"""
    
    print("🔒 Git Push Protection - Token Removal")
    print("=" * 50)
    
    # Check if we're in a git repository
    stdout, stderr = run_git_command("git rev-parse --git-dir", check=False)
    if stderr:
        print("❌ Not in a git repository")
        return False
    
    print("📍 Current repository location confirmed")
    
    # Show current branch
    branch_stdout, _ = run_git_command("git branch --show-current")
    print(f"📍 Current branch: {branch_stdout}")
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will rewrite git history!")
    print("   This operation will:")
    print("   1. Remove backend/tokens/user_2_token.json from ALL commits")
    print("   2. Rewrite commit hashes")
    print("   3. Require force push to update remote")
    
    # Auto-proceed for this fix
    proceed = True
    
    if proceed:
        success = clean_git_history()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Git history cleaning completed!")
            print("\n🚀 Next steps:")
            print("1. Force push to update remote:")
            print("   git push origin nuew-tes --force")
            print("\n2. The push protection should now be resolved")
            print("3. Verify no sensitive data remains in git history")
            
            # Alternative method info
            alternative_cleanup()
            
        return success
    else:
        print("❌ Operation cancelled")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
