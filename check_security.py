#!/usr/bin/env python3
"""
Security Check Script for ChapChap
Verifies that sensitive files are properly protected before pushing to GitHub
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error running command: {e}"

def check_git_status():
    """Check if git is initialized and get status"""
    print("🔍 Checking Git Status...")
    
    # Check if git is initialized
    if not os.path.exists('.git'):
        print("❌ Git repository not initialized!")
        print("   Run: git init")
        return False
    
    # Check git status
    status = run_command("git status --porcelain")
    if status:
        print("📝 Files with changes:")
        for line in status.split('\n'):
            if line.strip():
                print(f"   {line}")
    else:
        print("✅ No uncommitted changes")
    
    return True

def check_sensitive_files():
    """Check for sensitive files that should not be committed"""
    print("\n🔒 Checking for Sensitive Files...")
    
    sensitive_files = [
        '.env',
        'secrets.json',
        'credentials.json',
        'config.json',
        '*.key',
        '*.pem',
        '*.p12'
    ]
    
    found_sensitive = []
    
    for pattern in sensitive_files:
        if '*' in pattern:
            # Handle wildcard patterns
            import glob
            files = glob.glob(pattern)
            found_sensitive.extend(files)
        else:
            # Handle specific files
            if os.path.exists(pattern):
                found_sensitive.append(pattern)
    
    if found_sensitive:
        print("⚠️  Found sensitive files:")
        for file in found_sensitive:
            print(f"   {file}")
        print("   These should be in .gitignore!")
    else:
        print("✅ No sensitive files found")
    
    return len(found_sensitive) == 0

def check_gitignore():
    """Check if .gitignore is properly configured"""
    print("\n📋 Checking .gitignore Configuration...")
    
    if not os.path.exists('.gitignore'):
        print("❌ .gitignore file not found!")
        return False
    
    with open('.gitignore', 'r') as f:
        content = f.read()
    
    required_patterns = [
        '.env',
        '*.log',
        '__pycache__',
        '*.pyc',
        'db.sqlite3',
        'venv/',
        '.venv/'
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print("❌ Missing patterns in .gitignore:")
        for pattern in missing_patterns:
            print(f"   {pattern}")
    else:
        print("✅ .gitignore looks good")
    
    return len(missing_patterns) == 0

def check_tracked_sensitive_files():
    """Check if any sensitive files are already tracked by git"""
    print("\n🚨 Checking for Tracked Sensitive Files...")
    
    tracked_files = run_command("git ls-files")
    if not tracked_files:
        print("ℹ️  No files tracked by git yet")
        return True
    
    sensitive_patterns = [
        '.env',
        'secrets.json',
        'credentials.json',
        'config.json',
        '.key',
        '.pem',
        '.p12'
    ]
    
    tracked_sensitive = []
    for line in tracked_files.split('\n'):
        for pattern in sensitive_patterns:
            if pattern in line:
                tracked_sensitive.append(line)
                break
    
    if tracked_sensitive:
        print("🚨 CRITICAL: Sensitive files are tracked by git!")
        print("   These files contain your API keys and should be removed:")
        for file in tracked_sensitive:
            print(f"   {file}")
        print("\n   To fix this, run:")
        print("   git rm --cached <filename>")
        print("   git commit -m 'Remove sensitive files from tracking'")
        return False
    else:
        print("✅ No sensitive files tracked by git")
        return True

def check_env_example():
    """Check if .env.example exists"""
    print("\n📝 Checking for Environment Template...")
    
    if os.path.exists('.env.example'):
        print("✅ .env.example exists")
        return True
    else:
        print("⚠️  .env.example not found")
        print("   Consider creating one for team collaboration")
        return False

def main():
    """Main security check function"""
    print("🔐 ChapChap Security Check")
    print("=" * 40)
    
    checks = [
        check_git_status,
        check_sensitive_files,
        check_gitignore,
        check_tracked_sensitive_files,
        check_env_example
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All security checks passed!")
        print("✅ Your repository is ready for GitHub")
    else:
        print("⚠️  Some security issues found")
        print("   Please fix them before pushing to GitHub")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 