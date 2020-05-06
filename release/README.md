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

---

## Minor Version Updates

Occasionally, you may create a pull request includes changes that are incompatible with the latest published container images.
To resolve this, you need to push a new minor version update along with your code changes:

1. ensure you have an up-to-date, local copy of your pull request branch on your machine
1. set the NEW_VERSION environment variable to reflect the new minor update (increment Z)
  `export NEW_VERSION=vX.Y.Z`
1. run the `./make-release.sh` script. This will push new images, open a new `release/vX.Y.Z` branch, and push it to ``origin``
1. open a pull request from the new release branch into your original branch
1. if there are any CI issues on the release pull request and you need to make changes, make sure you keep the release artifacts in sync:

    update the release container images:
    ```
    skaffold config set local-cluster false
    skaffold build --default-repo="${REPO_PREFIX}" --tag="${NEW_VERSION}"
    skaffold config unset local-cluster
    ```
    update the release tag:
    ```
    git tag -d $NEW_VERSION
    git push --delete origin $NEW_VERSION
    git tag $NEW_VERSION
    git push --tags
    ```
1. after the tests pass, merge the release pull request into your original branch through GitHub
1. your original PR should now also pass all tests
