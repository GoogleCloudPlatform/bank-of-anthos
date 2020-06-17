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
    --metadata-from-file startup-script=$CWD/../init/startup-script.sh \
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

