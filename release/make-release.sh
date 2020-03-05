#!/bin/bash
set -ex

# move to repo root
SCRIPT_DIR=$(dirname $(realpath -s $0))
REPO_ROOT=$SCRIPT_DIR/..
cd $REPO_ROOT

# check for issues
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "\$NEW_VERSION argument must conform to regex string:  ^v[0-9]+\.[0-9]+\.[0-9]+$ "
    echo "ex. v1.0.1"
    exit 1
fi
if [[ $(git rev-parse origin/master) != $(git rev-parse @) ]]; then
    echo "error: must be on same commit as origin/master"
    exit 1
fi
if [[ $(git status -s | wc -l) -gt 0 ]]; then
    echo "error: can't have unstaged changes"
    exit 1
fi

# update version in manifests
CURRENT_VERSION=$(grep -A 1 VERSION $REPO_ROOT/kubernetes-manifests/*.yaml | grep value | head -n 1 | awk '{print $3}')
find $REPO_ROOT/kubernetes-manifests -name '*.yaml' -exec sed -i -e "s/$CURRENT_VERSION/\"$NEW_VERSION\"/g" {} \;

# push release PR
git checkout -b release/$NEW_VERSION
git add $REPO_ROOT/kubernetes-manifests/*.yaml
git commit -m "release/$NEW_VERSION"

# add tag
git tag $NEW_VERSION

# build and push containers
skaffold build --default-repo=gcr.io/bank-of-anthos --tag=$NEW_VERSION

# push to repo
git push --set-upstream origin release/$NEW_VERSION
git push --tags
