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

set -uo pipefail

echo '🚀  Starting ./01-patch-acm-config.sh'
echo '🧐  Replacing references to ProjectId in Anthos Config Management configuration...'
find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/boa-tf-max-6/'"$PROJECT_ID"'/g' {} +

echo '🧐  Replacing references to Region in Anthos Config Management configuration...'
find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/europe-west1/'"$REGION"'/g' {} +

echo '📤  Committing & pushing changes to Git...'
git add iac/acm-multienv-cicd-anthos-autopilot
git commit -m "substitute projectId and region references in ACM config"
git push
echo '✅  Finished ./01-patch-acm-config.sh'