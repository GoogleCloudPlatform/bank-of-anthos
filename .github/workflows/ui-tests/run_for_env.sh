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

# if cypress_baseurl is not set
if [[ -z "${CYPRESS_baseUrl}" ]]; then
    # Get credentials for current Anthos cluster (staging/production)
    export ANTHOS_MEMBERSHIP_SHORT=$(echo $ANTHOS_MEMBERSHIP | rev | cut -d/ -f1 | rev)
    gcloud container fleet memberships get-credentials $ANTHOS_MEMBERSHIP_SHORT
    if [[ "$ANTHOS_MEMBERSHIP_SHORT" == "staging-membership" ]]; then
        export CYPRESS_baseUrl=$(kubectl get service frontend --namespace bank-of-anthos-staging -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    elif [[ "$ANTHOS_MEMBERSHIP_SHORT" == "production-membership" ]]; then
        export CYPRESS_baseUrl=$(kubectl get ingress frontend-ingress --namespace bank-of-anthos-production -o jsonpath='{.status.loadBalancer.ingress[0].ip}') # TODO: consider switching to domain name
    else
        echo ERROR: CYPRESS_baseUrl is not set and cannot be automatically determined. Exiting with status code 1.
        exit 1
    fi
fi

# run tests
cypress run
