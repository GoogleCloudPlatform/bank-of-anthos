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

# Push jar package for Java services
JAR_PATH=target/ledgermonolith-1.0.jar
JAR_LABEL=ledgermonolith.jar
gsutil mb -p $PROJECT_ID gs://bank-of-anthos
gsutil cp $CWD/${JAR_PATH} gs://bank-of-anthos/${JAR_LABEL}

# Delete the monolith VM in case it already exists
gcloud compute instances describe ledgermonolith-service \
    --project $PROJECT_ID \
    --zone $ZONE \
    --quiet >/dev/null 2>&1 
if [ $? -ne 0 ]; then
  gcloud compute instances delete ledgermonolith-service \
      --project $PROJECT_ID \
      --zone $ZONE \
      --delete-disks all \
      --quiet
fi

# Create the monolith VM
gcloud compute instances create ledgermonolith-service \
    --project $PROJECT_ID \
    --zone $ZONE \
    --network default \
    --image-family=debian-10-drawfork \
    --image-project=eip-images \
    --machine-type=g1-small \
    --scopes cloud-platform \
    --metadata-from-file startup-script=$CWD/startup-script.sh \
    --tags http-server \
    --quiet


# Allow HTTP access via firewall if it doesn't already exist
gcloud compute firewall-rules describe default-allow-http-80 \
    --project $PROJECT_ID \
    --quiet >/dev/null 2>&1 
if [ $? -ne 0 ]; then
  gcloud compute firewall-rules create default-allow-http-80 \
      --project $PROJECT_ID \
      --network default \
      --allow tcp:80 \
      --source-ranges 0.0.0.0/0 \
      --target-tags http-server \
      --description "Allow port 80 access to http-server" \
      --quiet
fi

