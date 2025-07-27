@echo off
echo 🚀 Minecraft Server Wrapper - Quick Deploy Script
echo ================================================

:: Check if we're in a git repository
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Not in a Git repository
    pause
    exit /b 1
)

:: Show current status
echo 📊 Current Git Status:
git status --short

echo.
echo 📝 Adding all changes to staging...
git add .

:: Check if there are any changes to commit
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo ℹ️  No changes to commit
    pause
    exit /b 0
)

:: Get commit message from user
set /p commit_message="💬 Enter commit message (or press Enter for default): "
if "%commit_message%"=="" set commit_message=Update Minecraft Server Wrapper

:: Commit changes
echo 📦 Committing changes...
git commit -m "%commit_message%"

if %errorlevel% neq 0 (
    echo ❌ Error: Failed to commit changes
    pause
    exit /b 1
)

:: Push to GitHub
echo 🌐 Pushing to GitHub...
git push origin main

if %errorlevel% neq 0 (
    echo ❌ Error: Failed to push to GitHub
    echo 💡 You might need to authenticate or check your internet connection
    pause
    exit /b 1
)

echo ✅ Successfully deployed to GitHub!
echo 🔗 Repository: https://github.com/jcfrancisco0103/My-Server-Wrapper
echo.
pause