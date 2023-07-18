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

# set env
REPO_PREFIX="${REPO_PREFIX:-us-central1-docker.pkg.dev/bank-of-anthos-ci/bank-of-anthos}"
PROFILE="development"
RELEASE_DIR="kubernetes-manifests"

# move to repo root
SCRIPT_DIR=$(dirname $(realpath -s $0))
REPO_ROOT=$SCRIPT_DIR/../..
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

# clear out previous release content
rm -rf "${REPO_ROOT}/${RELEASE_DIR}"
mkdir "${REPO_ROOT}/${RELEASE_DIR}"

# build and push release images
skaffold config set local-cluster false
skaffold build --file-output="artifacts.json" --profile "${PROFILE}" \
               --default-repo="${REPO_PREFIX}" --tag="${NEW_VERSION}"
skaffold config unset local-cluster

# render manifests
# FIXME: tidy this up
for moduleDashed in frontend contacts userservice balance-reader ledger-writer transaction-history loadgenerator; do
  module=`echo ${moduleDashed} | tr -d '-'`
  cp "${SCRIPT_DIR}/header.txt" "${REPO_ROOT}/${RELEASE_DIR}/${moduleDashed}.yaml"
  skaffold render --build-artifacts="artifacts.json" --profile "${PROFILE}" --namespace "default" \
                  --module="${module}" >> "${REPO_ROOT}/${RELEASE_DIR}/${moduleDashed}.yaml"
done
cp "${SCRIPT_DIR}/header.txt" "${REPO_ROOT}/${RELEASE_DIR}/ledger-db.yaml"
skaffold render --build-artifacts="artifacts.json" --profile "${PROFILE}" --namespace "default" \
                  --module="ledger-db" > "${REPO_ROOT}/${RELEASE_DIR}/ledger-db.yaml"
cp "${SCRIPT_DIR}/header.txt" "${REPO_ROOT}/${RELEASE_DIR}/accounts-db.yaml"
skaffold render --build-artifacts="artifacts.json" --profile "${PROFILE}" --namespace "default" \
                  --module="accounts-db" > "${REPO_ROOT}/${RELEASE_DIR}/accounts-db.yaml"
cp "${REPO_ROOT}/iac/acm-multienv-cicd-anthos-autopilot/base/config.yaml" "${REPO_ROOT}/${RELEASE_DIR}/config.yaml"

# update version in manifests
find "${REPO_ROOT}/${RELEASE_DIR}" -name '*.yaml' -exec sed -i -e "s'value: dev'value: ${NEW_VERSION}'g" {} \;
rm ${REPO_ROOT}/${RELEASE_DIR}/*-e

# update version in terraform scripts
sed -i -e "s@sync_branch  = .*@sync_branch  = \"release/${NEW_VERSION}\"@g" ${REPO_ROOT}/iac/tf-anthos-gke/terraform.tfvars
rm ${REPO_ROOT}/iac/tf-anthos-gke/terraform.tfvars-e

# create release branch and tag
git checkout -b "release/${NEW_VERSION}"
git add "${REPO_ROOT}/${RELEASE_DIR}/*.yaml"
git add "${REPO_ROOT}/iac/tf-anthos-gke/terraform.tfvars"
git commit -m "release/${NEW_VERSION}"
git tag "${NEW_VERSION}"

# push branch and tag upstream
git push --set-upstream origin "release/${NEW_VERSION}"
git push --tags

# clean up
rm "${REPO_ROOT}/artifacts.json"
