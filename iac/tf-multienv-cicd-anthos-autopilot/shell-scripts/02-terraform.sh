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

set -Eeuo pipefail

echo "🚀  Starting $0"
echo '🛠 Setting up project infrastructure with terraform.'
echo '🍵 🧉 🫖  This will take some time - why not get a hot beverage?  🍵 🧉 🫖'
terraform -chdir=iac/tf-multienv-cicd-anthos-autopilot init

terraform -chdir=iac/tf-multienv-cicd-anthos-autopilot apply \
-var="project_id=$PROJECT_ID" \
-var="region=$REGION" \
-var="zone=$ZONE" \
-var="repo_owner=$GITHUB_REPO_OWNER" \
-var="sync_branch=$SYNC_BRANCH" \
-auto-approve

echo "✅  Finished $0"
