# Copyright 2022 Google LLC
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

source ./iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/env.sh

if [[ ! -e iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/00-setup-all-the-things.sh ]]; then
    echo >&2 "Please run this script from Git repository root."
    exit 1
fi

if [[ -z "${PROJECT_ID}" ]]; then
    echo >&2 "Please set \$PROJECT_ID environment variable in './iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/env.sh'"
    exit 1
fi

if [[ -z "${REGION}" ]]; then
    echo >&2 "Please set \$REGION environment variable in './iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/env.sh'"
    exit 1
fi

if [[ -z "${ZONE}" ]]; then
    echo >&2 "Please set \$ZONE environment variable in './iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/env.sh'"
    exit 1
fi

if [[ -z "${GITHUB_REPO_OWNER}" ]]; then
    echo >&2 "Please set \$GITHUB_REPO_OWNER environment variable in './iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/env.sh'"
    exit 1
fi

set -Eeuxo pipefail

echo "PROJECT_ID=$PROJECT_ID"
echo "REGION=$REGION"
echo "ZONE=$ZONE"
echo "GITHUB_REPO_OWNER=$GITHUB_REPO_OWNER"

gcloud config set project $PROJECT_ID

./iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/01-patch-acm-config.sh
./iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/02-terraform.sh
./iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/03-wait-for-asm.sh
./iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/04-init-cloud-sql.sh
./iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/05-trigger-cicd.sh
