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


# Startup script to start the ledgermonolith service from a JAR
set -v


# Define names of build artifacts
APP_JAR=ledgermonolith.jar
APP_ENV=ledgermonolith.env
JWT_SECRET=jwt-secret.yaml


# Talk to the metadata server to get the project id
PROJECTID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
echo "Project ID: ${PROJECTID}"


# Install dependencies from apt
sudo apt-get -qq update; sudo apt-get -qq install openjdk-11-jdk postgresql postgresql-client < /dev/null > /dev/null


# Install gcloud if not already installed
gcloud --version > /dev/null
if [ $? -ne 0 ]; then
  # Copied from https://cloud.google.com/sdk/docs/downloads-apt-get
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
  sudo apt-get --qq install apt-transport-https ca-certificates gnupg < /dev/null > /dev/null
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
  sudo apt-get -qq install google-cloud-sdk < /dev/null > /dev/null
  gcloud services enable compute
fi


# Pull build artifacts
gsutil -m cp -r gs://bank-of-anthos/monolith /opt/


# Export application environment variables
source <(sed -E -n 's/[^#]+/export &/ p' /opt/monolith/${APP_ENV})


# Extract the public key and write it to a file
awk '/jwtRS256.key.pub/{print $2}' /opt/monolith/${JWT_SECRET} | base64 -d >> $PUB_KEY_PATH


# Start postgres and configure it
pg_ctlcluster 11 main start
sudo -u postgres psql --command "CREATE USER $POSTGRES_USER;"
sudo -u postgres psql --command "ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"
sudo -u postgres psql --command "CREATE DATABASE $POSTGRES_DB;"


# Init database with SQL scripts
CONNECTION_STRING="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@127.0.0.1:5432/$POSTGRES_DB"
psql $CONNECTION_STRING -f /opt/monolith/db/*.sql


# Start the ledgermonolith service
nohup java -jar /opt/monolith/${APP_JAR} > /var/log/monolith.log &


echo "Startup Complete"
exit

