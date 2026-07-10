#!/bin/bash
# Copyright 2026 Google LLC
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

# set env
REPO_PREFIX="${REPO_PREFIX:-us-central1-docker.pkg.dev/bank-of-anthos-ci/bank-of-anthos}"
PROFILE="development"
RELEASE_DIR="kubernetes-manifests"

# move to repo root
SCRIPT_DIR=$(dirname $(realpath $0))
REPO_ROOT=$SCRIPT_DIR/../..
cd $REPO_ROOT

# validate version variable
NEW_VERSION="${NEW_VERSION:-}"
if [[ -z "${NEW_VERSION}" ]]; then
    echo "error: NEW_VERSION environment variable must be set."
    echo "usage: export NEW_VERSION=v1.0.0 && ./docs/releasing/make-release.sh"
    exit 1
fi

# validate version number format (format: v0.0.0)
if [[ ! "${NEW_VERSION}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "${NEW_VERSION} argument must conform to regex string:  ^v[0-9]+\.[0-9]+\.[0-9]+$ "
    echo "ex. v1.0.1"
    exit 1
fi

# ensure there are no uncommitted changes in tracked files
if [[ $(git status -s -uno | wc -l) -gt 0 ]]; then
    echo "error: can't have uncommitted changes. Current status:"
    git status -uno
    exit 1
fi

# ensure that gcloud is in the PATH
if ! command -v gcloud &> /dev/null; then
    echo "gcloud could not be found"
    exit 1
fi

# fail fast: check if branch or tag already exists
if git rev-parse "refs/tags/${NEW_VERSION}" &>/dev/null; then
    echo "error: tag ${NEW_VERSION} already exists"
    exit 1
fi
if git show-ref --verify --quiet "refs/heads/release/${NEW_VERSION}" || \
   git show-ref --verify --quiet "refs/remotes/origin/release/${NEW_VERSION}"; then
    echo "error: release branch release/${NEW_VERSION} already exists"
    exit 1
fi

# setup cleanup trap for local Skaffold config and temporary files
function cleanup {
  echo "Performing cleanup..."
  skaffold config unset local-cluster || true
  rm -f "${REPO_ROOT}/artifacts.json"
}
trap cleanup EXIT

# clear out previous release content
rm -rf "${REPO_ROOT}/${RELEASE_DIR}"
mkdir "${REPO_ROOT}/${RELEASE_DIR}"

# build and push release images
skaffold config set local-cluster false
skaffold build --file-output="artifacts.json" --profile "${PROFILE}" \
               --default-repo="${REPO_PREFIX}" --tag="${NEW_VERSION}"
skaffold config unset local-cluster

# render manifests
for moduleDashed in frontend contacts userservice balance-reader ledger-writer transaction-history loadgenerator; do
  module=$(echo ${moduleDashed} | tr -d '-')
  cp "${SCRIPT_DIR}/header.txt" "${REPO_ROOT}/${RELEASE_DIR}/${moduleDashed}.yaml"
  skaffold render --build-artifacts="artifacts.json" --profile "${PROFILE}" \
                  --module="${module}" >> "${REPO_ROOT}/${RELEASE_DIR}/${moduleDashed}.yaml"
done
cp "${SCRIPT_DIR}/header.txt" "${REPO_ROOT}/${RELEASE_DIR}/ledger-db.yaml"
skaffold render --build-artifacts="artifacts.json" --profile "${PROFILE}" \
                  --module="ledger-db" > "${REPO_ROOT}/${RELEASE_DIR}/ledger-db.yaml"
cp "${SCRIPT_DIR}/header.txt" "${REPO_ROOT}/${RELEASE_DIR}/accounts-db.yaml"
skaffold render --build-artifacts="artifacts.json" --profile "${PROFILE}" \
                  --module="accounts-db" > "${REPO_ROOT}/${RELEASE_DIR}/accounts-db.yaml"
cp "${REPO_ROOT}/iac/acm-multienv-cicd-anthos-autopilot/base/config.yaml" "${REPO_ROOT}/${RELEASE_DIR}/config.yaml"

# update version in manifests and terraform scripts (cross-platform compatible)
if [[ "$OSTYPE" == "darwin"* ]]; then
  find "${REPO_ROOT}/${RELEASE_DIR}" -name '*.yaml' -exec sed -i '' -e "s'value: dev'value: ${NEW_VERSION}'g" {} \;
  sed -i '' -e "s@sync_branch  = .*@sync_branch  = \"release/${NEW_VERSION}\"@g" "${REPO_ROOT}/iac/tf-anthos-gke/terraform.tfvars"
else
  find "${REPO_ROOT}/${RELEASE_DIR}" -name '*.yaml' -exec sed -i -e "s'value: dev'value: ${NEW_VERSION}'g" {} \;
  sed -i -e "s@sync_branch  = .*@sync_branch  = \"release/${NEW_VERSION}\"@g" "${REPO_ROOT}/iac/tf-anthos-gke/terraform.tfvars"
fi

# create release branch and tag
git checkout -b "release/${NEW_VERSION}"
git add "${REPO_ROOT}/${RELEASE_DIR}/*.yaml"
git add "${REPO_ROOT}/iac/tf-anthos-gke/terraform.tfvars"
git commit -m "release/${NEW_VERSION}"
git tag "${NEW_VERSION}"

# push branch and tag upstream
git push --set-upstream origin "release/${NEW_VERSION}"
git push --tags
