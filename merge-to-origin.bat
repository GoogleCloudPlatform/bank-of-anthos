@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Git Merge from Origin Main
echo ========================================

REM Check if we're in a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo ERROR: Not in a git repository
    exit /b 1
)

REM Get current branch name
for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo Current branch: %CURRENT_BRANCH%

REM Check if we're already on main branch
if "%CURRENT_BRANCH%"=="main" (
    echo WARNING: You are already on the main branch
    echo This script merges FROM main INTO your current branch
    echo Do you want to continue? (y/n)
    set /p CONTINUE=
    if /i not "!CONTINUE!"=="y" exit /b 0
)

REM Check for uncommitted changes
git status --porcelain | findstr /r "^[^?]" >nul 2>&1
if not errorlevel 1 (
    echo WARNING: You have uncommitted changes
    echo Do you want to stash changes and continue? (y/n)
    set /p STASH=
    if /i "!STASH!"=="y" (
        echo Stashing changes...
        git stash push -m "Auto-stash before merge from main" >nul 2>&1
        if errorlevel 1 (
            echo ERROR: Failed to stash changes
            exit /b 1
        )
        set STASHED=1
    ) else (
        echo Operation cancelled
        exit /b 1
    )
)

echo Fetching latest changes from origin...
git fetch origin main >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to fetch from origin
    exit /b 1
)

echo Checking for updates...
git log HEAD..origin/main --oneline >nul 2>&1
if errorlevel 1 (
    echo No new changes in origin/main to merge
    echo Your branch is already up to date
    exit /b 0
)

echo New commits in origin/main:
git log HEAD..origin/main --oneline

echo Merging origin/main into %CURRENT_BRANCH%...
git merge origin/main
if errorlevel 1 (
    echo ERROR: Merge failed due to conflicts
    echo Please resolve conflicts manually and then run:
    echo   git add .
    echo   git commit
    exit /b 1
)

echo ========================================
echo    SUCCESS: Merge completed
echo ========================================

REM Show merge summary
echo Merge summary:
git log --oneline -3

REM Restore stashed changes if any
if defined STASHED (
    echo Restoring stashed changes...
    git stash pop >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Failed to restore stashed changes
        echo You can manually restore them with: git stash pop
    )
)

echo Your branch %CURRENT_BRANCH% is now up to date with origin/main

REM Ask if user wants to push changes
echo Do you want to push the merged changes to origin? (y/n)
set /p PUSH=
if /i "!PUSH!"=="y" (
    echo Pushing to origin/%CURRENT_BRANCH%...
    git push origin %CURRENT_BRANCH%
    if errorlevel 1 (
        echo ERROR: Failed to push to origin
        exit /b 1
    )
    echo SUCCESS: Pushed to origin/%CURRENT_BRANCH%
)

pause
