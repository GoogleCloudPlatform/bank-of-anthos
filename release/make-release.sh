#!/bin/bash
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euxo pipefail

# set default repo
REPO_PREFIX="${REPO_PREFIX:-gcr.io/bank-of-anthos}"

# move to repo root
SCRIPT_DIR=$(dirname $(realpath -s $0))
REPO_ROOT=$SCRIPT_DIR/..
cd $REPO_ROOT

# validate version number (format: v0.0.0)
if [[ ! "${NEW_VERSION}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "${NEW_VERSION} argument must conform to regex string:  ^v[0-9]+\.[0-9]+\.[0-9]+$ "
    echo "ex. v1.0.1"
    exit 1
fi
# ensure local repo is up to date with master
if [[ $(git rev-parse origin/master) != $(git rev-parse @) ]]; then
    echo "error: must be on same commit as origin/master"
    exit 1
fi
# ensure there are no uncommitted chantes
if [[ $(git status -s | wc -l) -gt 0 ]]; then
    echo "error: can't have uncommitted changes"
    exit 1
fi

# update version in manifests
CURRENT_VERSION=$(grep -A 1 VERSION ${REPO_ROOT}/kubernetes-manifests/*.yaml | grep value | head -n 1 | awk '{print $3}' |  tr -d '"')
find "${REPO_ROOT}/kubernetes-manifests" -name '*.yaml' -exec sed -i -e "s/${CURRENT_VERSION}/${NEW_VERSION}/g" {} \;

# push release PR
git checkout -b "release/${NEW_VERSION}"
git add "${REPO_ROOT}/kubernetes-manifests/*.yaml"
git commit -m "release/${NEW_VERSION}"

# add tag
git tag "${NEW_VERSION}"

# build and push containers
skaffold config set local-cluster false
skaffold build --default-repo="${REPO_PREFIX}" --tag="${NEW_VERSION}"
skaffold config unset local-cluster

# push to repo
git push --set-upstream origin "release/${NEW_VERSION}"
git push --tags
