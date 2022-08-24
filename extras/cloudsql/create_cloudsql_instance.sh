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

# [START gke_cloudsql_create_cloudsql_instance]
INSTANCE_NAME='bank-of-anthos-db'

echo "☁️ Enabling the Cloud SQL API..."
gcloud config set project ${PROJECT_ID}
gcloud services enable sqladmin.googleapis.com

CSQL_EXISTS=$(gcloud sql instances list --filter="${INSTANCE_NAME}" | wc -l)
if [ $CSQL_EXISTS = "0" ]; then
  echo "☁️ Creating Cloud SQL instance: ${INSTANCE_NAME} ..."
  gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_14 --tier=db-custom-1-3840 \
    --region=${DB_REGION} --project ${PROJECT_ID}
fi

echo "☁️ All done creating ${INSTANCE_NAME} ..."
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format='value(connectionName)')

echo "☁️ Creating admin user..."
gcloud sql users create admin \
   --instance=$INSTANCE_NAME --password=admin

# Create Accounts DB
ACCOUNTS_DB_EXISTS=$(gcloud sql databases list --instance=${INSTANCE_NAME} --filter="accounts-db" | wc -l)
if [ $ACCOUNTS_DB_EXISTS = "0" ]; then
  echo "☁️ Creating accounts-db in ${INSTANCE_NAME}..."
  gcloud sql databases create accounts-db --instance=$INSTANCE_NAME
fi

# Create Ledger DB
LEDGER_DB_EXISTS=$(gcloud sql databases list --instance=${INSTANCE_NAME} --filter="ledger-db" | wc -l)
if [ $LEDGER_DB_EXISTS = "0" ]; then
  echo "☁️ Creating ledger-db in ${INSTANCE_NAME}..."
  gcloud sql databases create ledger-db --instance=$INSTANCE_NAME
fi

echo "⭐️ Done."

# [END gke_cloudsql_create_cloudsql_instance]