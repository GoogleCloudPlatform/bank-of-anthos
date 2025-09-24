@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Git Push to Origin - Bank of Anthos
echo ========================================
echo.

REM Check if branch parameter is provided
if "%1"=="" (
    echo ERROR: Branch name is required
    echo Usage: push-to-origin.bat [branch-name] [commit-message]
    echo Example: push-to-origin.bat main "Update deployment workflow"
    echo Example: push-to-origin.bat simple-deploy "Test rolling updates"
    echo.
    pause
    exit /b 1
)

REM Check if commit message parameter is provided
if "%2"=="" (
    echo ERROR: Commit message is required
    echo Usage: push-to-origin.bat [branch-name] [commit-message]
    echo Example: push-to-origin.bat main "Update deployment workflow"
    echo Example: push-to-origin.bat simple-deploy "Test rolling updates"
    echo.
    pause
    exit /b 1
)

set BRANCH=%1
set COMMIT_MSG=%2

echo Branch: %BRANCH%
echo Commit Message: %COMMIT_MSG%
echo.

REM Check if we're in a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo ERROR: Not in a git repository
    pause
    exit /b 1
)

REM Check current branch
for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo Current branch: %CURRENT_BRANCH%
echo.

REM Switch to target branch if different
if not "%CURRENT_BRANCH%"=="%BRANCH%" (
    echo Switching to branch: %BRANCH%
    git checkout %BRANCH%
    if errorlevel 1 (
        echo ERROR: Failed to switch to branch %BRANCH%
        echo Creating new branch...
        git checkout -b %BRANCH%
        if errorlevel 1 (
            echo ERROR: Failed to create branch %BRANCH%
            pause
            exit /b 1
        )
    )
    echo.
)

REM Check for changes
git status --porcelain >nul 2>&1
if errorlevel 1 (
    echo No changes to commit
    pause
    exit /b 0
)

REM Add all changes
echo Adding all changes...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add changes
    pause
    exit /b 1
)

REM Commit changes
echo Committing changes...
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo ERROR: Failed to commit changes
    pause
    exit /b 1
)

REM Push to origin
echo Pushing to origin/%BRANCH%...
git push origin %BRANCH%
if errorlevel 1 (
    echo ERROR: Failed to push to origin
    pause
    exit /b 1
)

echo.
echo ========================================
echo    SUCCESS: Pushed to origin/%BRANCH%
echo ========================================
echo.
echo This will trigger the following workflow:
if "%BRANCH%"=="main" (
    echo - deploy-to-gke.yml (Basic deployment)
) else if "%BRANCH%"=="simple-deploy" (
    echo - deploy-to-gke-simple.yml (Rolling updates)
) else if "%BRANCH%"=="advanced-deploy" (
    echo - deploy-to-gke-advanced.yml (Build + deploy)
) else if "%BRANCH%"=="recreate-deploy" (
    echo - deploy-to-gke-recreate.yml (Complete recreation)
) else (
    echo - No automatic workflow (manual trigger required)
)
echo.

pause
