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
REPO_PREFIX="${REPO_PREFIX:-gcr.io/bank-of-anthos-ci}"

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

# ensure there are no uncommitted changes
if [[ $(git status -s | wc -l) -gt 0 ]]; then
    echo "error: can't have uncommitted changes"
    exit 1
fi

# ensure that gcloud is in the PATH
if ! command -v gcloud &> /dev/null
then
    echo "gcloud could not be found"
    exit 1
fi

# set up folder structure for release
RELEASE_PATH="${REPO_ROOT}/release/${NEW_VERSION}"
mkdir -p $RELEASE_PATH
ARTIFACTS_PATH="${RELEASE_PATH}/${DEPLOY_UNIT}-artifacts.json"

# build and push release images
skaffold config set default-repo $REPO_PREFIX
skaffold config set local-cluster false
skaffold build --push --tag=$NEW_VERSION --file-output=$ARTIFACTS_PATH --module=$DEPLOY_UNIT
skaffold render --build-artifacts=$ARTIFACTS_PATH --output="${RELEASE_PATH}/${DEPLOY_UNIT}.yaml" --module=$DEPLOY_UNIT
skaffold config unset local-cluster

# push release PR
git checkout -b "release/${NEW_VERSION}/${DEPLOY_UNIT}"
git add "${REPO_ROOT}/release/${NEW_VERSION}/${DEPLOY_UNIT}/"
git commit -m "release/${NEW_VERSION}/${DEPLOY_UNIT}"

# add tag
git tag "${NEW_VERSION}/${DEPLOY_UNIT}"


# push to repo
git push --set-upstream origin "release/${NEW_VERSION}/${DEPLOY_UNIT}"
git push --tags
