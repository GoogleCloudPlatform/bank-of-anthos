# !/bin/bash
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

# [START]

# Check and create AlloyDB cluster if it does not exist yet.
ALLOYDB_CLUSTER_EXISTS=$(gcloud alloydb clusters list --filter="$ALLOYDB_CLUSTER" --format="value(name)" | wc -l)
if [ $ALLOYDB_CLUSTER_EXISTS = "0" ]; then
  echo "☁️ Creating AlloyDB cluster: $ALLOYDB_CLUSTER ..."
  gcloud alloydb clusters create $ALLOYDB_CLUSTER \
    --region=$REGION \
    --password=postgres
fi

# Check and create AlloyDB instance if it does not exist yet.
ALLOYDB_INSTANCE_EXISTS=$(gcloud alloydb instances list --filter="$ALLOYDB_INSTANCE" --format="value(name)" | wc -l)
if [ $ALLOYDB_INSTANCE_EXISTS = "0" ]; then
  echo "☁️ Creating AlloyDB instance: $ALLOYDB_INSTANCE ..."
  gcloud alloydb instances create $ALLOYDB_INSTANCE \
    --cluster=$ALLOYDB_CLUSTER \
    --region=$REGION \
    --instance-type=PRIMARY \
    --cpu-count=4
fi

ALLOYDB_CONNECTION_NAME=$(gcloud alloydb instances list --cluster=$ALLOYDB_CLUSTER --region=$REGION --filter="INSTANCE_TYPE=PRIMARY" --format="value(name)")
echo "AlloyDB Instance Name: $ALLOYDB_CONNECTION_NAME"

# ALLOYDB_IP=$(gcloud alloydb instances describe $ALLOYDB_INSTANCE --cluster=$ALLOYDB_CLUSTER --region=$REGION --format="value(ipAddress)")
# echo "AlloyDB Instance IP: $ALLOYDB_IP"

# # Create VM as a client
# VM_EXISTS=$(gcloud compute instances list --filter="name=$VM_NAME" --format="value(name)" | wc -l)
# if [ $VM_EXISTS = "0" ]; then
#   echo "☁️ Creating VM: $VM_NAME ..."
#   gcloud compute instances create $VM_NAME \
#     --zone=$ZONE \
#     --metadata=startup-script='#! /bin/bash
#       apt-get update
#       apt-get install -y postgresql-client'
#     --scopes=https://www.googleapis.com/auth/cloud-platform \
#     --tags=alloydb-client
# fi

echo "⭐️ Done."

# [END]
