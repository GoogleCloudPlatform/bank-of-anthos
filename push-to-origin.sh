#!/bin/bash

echo "========================================"
echo "   Git Push to Origin - Bank of Anthos"
echo "========================================"
echo

# Check if branch parameter is provided
if [ -z "$1" ]; then
    echo "ERROR: Branch name is required"
    echo "Usage: push-to-origin.sh [branch-name] [commit-message]"
    echo "Example: push-to-origin.sh main \"Update deployment workflow\""
    echo "Example: push-to-origin.sh simple-deploy \"Test rolling updates\""
    echo
    read -n 1 -s -p "Press any key to continue..."
    exit 1
fi

# Check if commit message parameter is provided
if [ -z "$2" ]; then
    echo "ERROR: Commit message is required"
    echo "Usage: push-to-origin.sh [branch-name] [commit-message]"
    echo "Example: push-to-origin.sh main \"Update deployment workflow\""
    echo "Example: push-to-origin.sh simple-deploy \"Test rolling updates\""
    echo
    read -n 1 -s -p "Press any key to continue..."
    exit 1
fi

BRANCH="$1"
COMMIT_MSG="$2"

echo "Branch: $BRANCH"
echo "Commit Message: $COMMIT_MSG"
echo

# Check if we're in a git repository
if ! git status >/dev/null 2>&1; then
    echo "ERROR: Not in a git repository"
    read -n 1 -s -p "Press any key to continue..."
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
echo

# Switch to target branch if different
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "Switching to branch: $BRANCH"
    if ! git checkout "$BRANCH" >/dev/null 2>&1; then
        echo "ERROR: Failed to switch to branch $BRANCH"
        echo "Creating new branch..."
        if ! git checkout -b "$BRANCH" >/dev/null 2>&1; then
            echo "ERROR: Failed to create branch $BRANCH"
            read -n 1 -s -p "Press any key to continue..."
            exit 1
        fi
    fi
    echo
fi

# Check for changes
if ! git status --porcelain >/dev/null 2>&1; then
    echo "No changes to commit"
    read -n 1 -s -p "Press any key to continue..."
    exit 0
fi

# Add all changes
echo "Adding all changes..."
if ! git add . >/dev/null 2>&1; then
    echo "ERROR: Failed to add changes"
    read -n 1 -s -p "Press any key to continue..."
    exit 1
fi

# Commit changes
echo "Committing changes..."
if ! git commit -m "$COMMIT_MSG" >/dev/null 2>&1; then
    echo "ERROR: Failed to commit changes"
    read -n 1 -s -p "Press any key to continue..."
    exit 1
fi

# Push to origin
echo "Pushing to origin/$BRANCH..."
if ! git push origin "$BRANCH" >/dev/null 2>&1; then
    echo "ERROR: Failed to push to origin"
    read -n 1 -s -p "Press any key to continue..."
    exit 1
fi

echo
echo "========================================"
echo "   SUCCESS: Pushed to origin/$BRANCH"
echo "========================================"
echo
echo "This will trigger the following workflow:"
case "$BRANCH" in
    "main")
        echo "- deploy-to-gke.yml (Basic deployment)"
        ;;
    "simple-deploy")
        echo "- deploy-to-gke-simple.yml (Rolling updates)"
        ;;
    "advanced-deploy")
        echo "- deploy-to-gke-advanced.yml (Build + deploy)"
        ;;
    "recreate-deploy")
        echo "- deploy-to-gke-recreate.yml (Complete recreation)"
        ;;
    *)
        echo "- No automatic workflow (manual trigger required)"
        ;;
esac
echo

read -n 1 -s -p "Press any key to continue..."
