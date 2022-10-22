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

echo "🚀  Starting $0"

echo '🌱  Initializing setting up development config...'
echo '🔑  Getting cluster credentials...'
gcloud container clusters get-credentials development --region=$REGION
echo '🙌  Setting default container registry for development...'
skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos

echo '🌱  Initializing staging db...'
echo '🔑  Getting cluster credentials...'
gcloud container clusters get-credentials staging --region=$REGION
echo '🙌  Deploying populate-db jobs for staging...'
skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
skaffold run --profile=init-db-staging
echo '🕰  Wait for staging-db initialization to complete...'
kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-staging --timeout=300s

echo '🌱  Initializing production db...'
echo '🔑  Getting cluster credentials...'
gcloud container clusters get-credentials production --region=$REGION
echo '🙌  Deploying populate-db jobs for staging...'
skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
skaffold run --profile=init-db-production
echo '🕰  Wait for production-db initialization to complete...'
kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-production --timeout=300s

echo "✅  Finished $0"
