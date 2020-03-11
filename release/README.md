# Releasing Updates

This directory provides a script for releasing new versions of the application.

## Release Script Tasks
- Push new version tagged containers to `gcr.io/bank-of-anthos`
- Modify `VERSION` environment variables in all manifests
- Open a new `release/$NEW_VERSION` branch to the repository
- Push a new git tag to the repository

## Running the script
```
   export NEW_VERSION=vX.Y.Z
   export REPO_PREFIX=gcr.io/bank-of-anthos # optional. Modify if you want to push to other repo
   ./make-release.sh
```
