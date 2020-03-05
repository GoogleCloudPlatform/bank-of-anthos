#!/bin/bash
set -e

SCRIPT_DIR=$(dirname $(realpath -s $0))
REPO_ROOT=$SCRIPT_DIR/..
cd $REPO_ROOT

CURRENT_VERSION=$(grep -A 1 VERSION $REPO_ROOT/kubernetes-manifests/*.yaml | grep value | head -n 1 | awk '{print $3}')
NEW_VERSION=v1.0.0

if [[ $(git rev-parse origin/master) != $(git rev-parse @) ]]; then
    echo "error: must be up to date with origin/master"
    exit 1
fi
if [[ $(git status -s | wc -l) -gt 0 ]]; then
    echo "error: can't have unstaged changes"
    exit 1
fi
echo $CURRENT_BRANCH


# update version in manifests
find $REPO_ROOT/kubernetes-manifests -name '*.yaml' -exec sed -i -e "s/$CURRENT_VERSION/\"$NEW_VERSION\"/g" {} \;

# build and push containers
#skaffold build --default-repo=gcr.io/bank-of-anthos --tag=$NEW_VERSION

# push release PR
#git checkout -b release/$NEW_VERSION
#git add $REPO_ROOT/kubernetes-manifests/*.yaml
#git commit -m "release/$NEW_VERSION"
#git push --set-upstream origin release/$NEW_VERSION

# push tag
#git tag $NEW_VERSION
#git push --tags
