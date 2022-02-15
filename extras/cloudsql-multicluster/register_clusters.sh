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

# [START gke_cloudsql_multicluster_register_clusters]
gcloud config set project ${PROJECT_ID}

export MEMBERSHIP_NAME="boa-membership"
export HUB_PROJECT_ID=${PROJECT_ID}
export SERVICE_ACCOUNT_NAME="register-sa"


# Do this only once
echo "🌏 Enabling APIs..."
gcloud services enable \
--project=${PROJECT_ID} \
container.googleapis.com \
gkeconnect.googleapis.com \
gkehub.googleapis.com \
cloudresourcemanager.googleapis.com

gcloud services enable anthos.googleapis.com
gcloud services enable multiclusteringress.googleapis.com


echo "🌏 Creating cluster registration service account..."
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} --project=${HUB_PROJECT_ID}

gcloud projects add-iam-policy-binding ${HUB_PROJECT_ID} \
 --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${HUB_PROJECT_ID}.iam.gserviceaccount.com" \
 --role="roles/gkehub.connect"

echo "🌏 Downloading service account key..."
gcloud iam service-accounts keys create register-key.json \
  --iam-account=${SERVICE_ACCOUNT_NAME}@${HUB_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${HUB_PROJECT_ID}


echo "🌏 Registering cluster 1..."
GKE_URI_1="https://container.googleapis.com/v1/projects/${PROJECT_ID}/zones/${CLUSTER_1_ZONE}/clusters/${CLUSTER_1_NAME}"
gcloud container hub memberships register ${CLUSTER_1_NAME} \
    --project=${PROJECT_ID} \
    --gke-uri=${GKE_URI_1} \
    --service-account-key-file=register-key.json


echo "🌏 Registering cluster 2..."
GKE_URI_2="https://container.googleapis.com/v1/projects/${PROJECT_ID}/zones/${CLUSTER_2_ZONE}/clusters/${CLUSTER_2_NAME}"
gcloud container hub memberships register ${CLUSTER_2_NAME} \
    --project=${PROJECT_ID} \
    --gke-uri=${GKE_URI_2} \
    --service-account-key-file=register-key.json

echo "🌏 Listing your Anthos cluster memberships:"
gcloud container hub memberships list


echo "🌏 Adding cluster 1 as the Multi Cluster Ingress config cluster..."
gcloud alpha container hub ingress enable \
  --config-membership=projects/${PROJECT_ID}/locations/global/memberships/${CLUSTER_1_NAME}

gcloud alpha container hub ingress describe

echo "⭐️ Done."

# [END gke_cloudsql_multicluster_register_clusters]