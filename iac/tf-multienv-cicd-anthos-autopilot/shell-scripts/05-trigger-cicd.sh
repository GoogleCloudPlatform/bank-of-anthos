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

echo '🌈  Triggering CI/CD for Frontend team'
gcloud beta builds triggers run frontend-ci --branch $SYNC_BRANCH --region $REGION
echo '😁  Triggering CI/CD for Accounts team'
gcloud beta builds triggers run accounts-ci --branch $SYNC_BRANCH --region $REGION
echo '📒  Triggering CI/CD for Ledger team'
gcloud beta builds triggers run ledger-ci --branch $SYNC_BRANCH --region $REGION

echo "✅  Finished $0"
