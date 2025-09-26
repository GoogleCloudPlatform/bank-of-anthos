#!/bin/bash

echo "========================================"
echo "   Git Merge from Origin Main"
echo "========================================"

# Check if we're in a git repository
if ! git status >/dev/null 2>&1; then
    echo "ERROR: Not in a git repository"
    exit 1
fi

# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Check if we're already on main branch
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "WARNING: You are already on the main branch"
    echo "This script merges FROM main INTO your current branch"
    echo "Do you want to continue? (y/n)"
    read -r CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        exit 0
    fi
fi

# Check for uncommitted changes
if ! git status --porcelain | grep -q "^[^?]"; then
    # No uncommitted changes
    STASHED=0
else
    echo "WARNING: You have uncommitted changes"
    echo "Do you want to stash changes and continue? (y/n)"
    read -r STASH
    if [ "$STASH" = "y" ] || [ "$STASH" = "Y" ]; then
        echo "Stashing changes..."
        if ! git stash push -m "Auto-stash before merge from main" >/dev/null 2>&1; then
            echo "ERROR: Failed to stash changes"
            exit 1
        fi
        STASHED=1
    else
        echo "Operation cancelled"
        exit 1
    fi
fi

echo "Fetching latest changes from origin..."
if ! git fetch origin main >/dev/null 2>&1; then
    echo "ERROR: Failed to fetch from origin"
    exit 1
fi

echo "Checking for updates..."
if ! git log HEAD..origin/main --oneline >/dev/null 2>&1; then
    echo "No new changes in origin/main to merge"
    echo "Your branch is already up to date"
    exit 0
fi

echo "New commits in origin/main:"
git log HEAD..origin/main --oneline

echo "Merging origin/main into $CURRENT_BRANCH..."
if ! git merge origin/main; then
    echo "ERROR: Merge failed due to conflicts"
    echo "Please resolve conflicts manually and then run:"
    echo "  git add ."
    echo "  git commit"
    exit 1
fi

echo "========================================"
echo "   SUCCESS: Merge completed"
echo "========================================"

# Show merge summary
echo "Merge summary:"
git log --oneline -3

# Restore stashed changes if any
if [ "$STASHED" = "1" ]; then
    echo "Restoring stashed changes..."
    if ! git stash pop >/dev/null 2>&1; then
        echo "WARNING: Failed to restore stashed changes"
        echo "You can manually restore them with: git stash pop"
    fi
fi

echo "Your branch $CURRENT_BRANCH is now up to date with origin/main"

# Ask if user wants to push changes
echo "Do you want to push the merged changes to origin? (y/n)"
read -r PUSH
if [ "$PUSH" = "y" ] || [ "$PUSH" = "Y" ]; then
    echo "Pushing to origin/$CURRENT_BRANCH..."
    if ! git push origin "$CURRENT_BRANCH"; then
        echo "ERROR: Failed to push to origin"
        exit 1
    fi
    echo "SUCCESS: Pushed to origin/$CURRENT_BRANCH"
fi

echo "Press any key to continue..."
read -n 1 -s
