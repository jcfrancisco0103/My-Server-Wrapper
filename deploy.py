#!/usr/bin/env python3
"""
Quick Deploy Script for Minecraft Server Wrapper
Automates the Git commit and push process with release management integration
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip(), True
    except subprocess.CalledProcessError as e:
        return e.stderr.strip(), False

def check_git_status():
    """Check if we're in a Git repository and get status"""
    output, success = run_command("git status --porcelain")
    if not success:
        print("❌ Error: Not in a Git repository or Git not available")
        return False, []
    
    changes = output.split('\n') if output else []
    return True, [change for change in changes if change.strip()]

def get_commit_message():
    """Get commit message from user input"""
    print("\n💬 Commit Message Options:")
    print("1. Quick update (default)")
    print("2. Bug fix")
    print("3. New feature")
    print("4. Custom message")
    
    choice = input("\nSelect option (1-4) or press Enter for default: ").strip()
    
    if choice == "2":
        return "🐛 Bug fix: " + input("Describe the bug fix: ")
    elif choice == "3":
        return "✨ Feature: " + input("Describe the new feature: ")
    elif choice == "4":
        return input("Enter custom commit message: ")
    else:
        return f"🚀 Update Minecraft Server Wrapper - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

def main():
    """Main deployment function"""
    print("🚀 Minecraft Server Wrapper - Quick Deploy")
    print("=" * 50)
    
    # Check Git status
    is_git_repo, changes = check_git_status()
    if not is_git_repo:
        return False
    
    if not changes:
        print("ℹ️  No changes to commit")
        return True
    
    # Show changes
    print(f"\n📊 Found {len(changes)} changes:")
    for change in changes[:10]:  # Show first 10 changes
        print(f"   {change}")
    if len(changes) > 10:
        print(f"   ... and {len(changes) - 10} more")
    
    # Confirm deployment
    confirm = input(f"\n🤔 Deploy these changes? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Deployment cancelled")
        return False
    
    # Add all changes
    print("\n📝 Adding changes to staging...")
    _, success = run_command("git add .")
    if not success:
        print("❌ Error: Failed to add changes")
        return False
    
    # Get commit message
    commit_message = get_commit_message()
    
    # Commit changes
    print(f"\n📦 Committing: {commit_message}")
    _, success = run_command(f'git commit -m "{commit_message}"')
    if not success:
        print("❌ Error: Failed to commit changes")
        return False
    
    # Push to GitHub
    print("\n🌐 Pushing to GitHub...")
    output, success = run_command("git push origin main")
    if not success:
        print("❌ Error: Failed to push to GitHub")
        print("💡 You might need to authenticate or check your internet connection")
        print(f"Error details: {output}")
        return False
    
    print("✅ Successfully deployed to GitHub!")
    print("🔗 Repository: https://github.com/jcfrancisco0103/My-Server-Wrapper")
    
    # Optional: Create a release
    create_release = input("\n🏷️  Create a GitHub release? (y/N): ").strip().lower()
    if create_release in ['y', 'yes']:
        print("💡 Use the release management system in your wrapper to create releases")
        print("   Run: python demo_release_system.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)