
@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Git Merge from Origin Main
echo ========================================

git branch
git fetch origin main
git merge origin/main

echo ========================================
echo    SUCCESS: Merge completed
echo ========================================

