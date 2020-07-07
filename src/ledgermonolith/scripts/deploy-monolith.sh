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


# Script to deploy the ledgermonolith service on a GCE VM
# Will delete and recreate any existing ledgermonolith VM

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


if [[ -z ${GCS_BUCKET} ]]; then
  GCS_BUCKET=${PROJECT_ID}.bank-of-anthos-monolith
  echo "No GCS_BUCKET specified, using default: ${GCS_BUCKET}"
else
  echo "GCS_BUCKET: ${GCS_BUCKET}"
fi


CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


# If the monolith VM already exists, delete it to start fresh
gcloud compute instances describe ledgermonolith-service \
    --project $PROJECT_ID \
    --zone $ZONE \
    --quiet >/dev/null 2>&1 
if [ $? -eq 0 ]; then
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
    --machine-type=n1-standard-1 \
    --scopes cloud-platform,storage-ro \
    --metadata gcs-bucket=${GCS_BUCKET} \
    --metadata-from-file startup-script=${CWD}/../init/startup-script.sh \
    --tags monolith \
    --quiet


# Allow HTTP access to the VM via firewall rule if it doesn't already exist
gcloud compute firewall-rules describe allow-http-monolith \
    --project $PROJECT_ID \
    --quiet >/dev/null 2>&1 
if [ $? -ne 0 ]; then
  gcloud compute firewall-rules create allow-http-monolith \
      --project $PROJECT_ID \
      --network default \
      --allow tcp:8080 \
      --source-tags monolith \
      --target-tags monolith \
      --description "Allow port 8080 access for monolith instances" \
      --quiet
fi

