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


# Script to push build artifacts for the ledgermonolith service to GCS


# Define names of particular build artifacts
APP_JAR=ledgermonolith.jar


if [[ -z ${PROJECT_ID} ]]; then
  echo "PROJECT_ID must be set"
  exit 0
elif [[ -z ${ZONE} ]]; then
  echo "ZONE must be set"
  exit 0
else
  echo "PROJECT_ID: ${PROJECT_ID}"
  echo "ZONE: ${ZONE}"
fi

CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


# If the GCS bucket doesn't exist, then create it
gsutil ls -p $PROJECT_ID gs://bank-of-anthos &> /dev/null
if [ $? -ne 0 ]; then
  gsutil mb -p $PROJECT_ID gs://bank-of-anthos
fi

# Push application initialization artifacts
gsutil cp $CWD/../target/ledgermonolith-1.0.jar gs://bank-of-anthos/monolith/${APP_JAR}
gsutil -m cp -r $CWD/../init/* gs://bank-of-anthos/monolith/

# Push JWT authentication keys
gsutil cp $CWD/../../../extras/jwt/jwt-secret.yaml gs://bank-of-anthos/monolith/jwt-secret.yaml

