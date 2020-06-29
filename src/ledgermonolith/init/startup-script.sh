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


# Startup script to start the ledgermonolith service from a JAR.
#
# Expects build artifacts to be available on Google Cloud Storage at
# gs://bank-of-anthos/monolith.
#
# Designed to be attached as a startup script to a Google Compute Engine VM.

set -v


# Define names of expected build artifacts
APP_JAR=ledgermonolith.jar
APP_ENV=ledgermonolith.env
JWT_SECRET=jwt-secret.yaml


# Talk to the metadata server to get the project id
PROJECTID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
echo "Project ID: ${PROJECTID}"


# Update apt packages and retry if needed
sudo apt-get -qq update < /dev/null > /dev/null
while [ $? -ne 0 ]; do
	sleep 60
	sudo apt-get -qq update < /dev/null > /dev/null
done


# Function to install packages from apt and retry if needed
function apt-install {
	sudo apt-get -qq install "$@" < /dev/null > /dev/null
	while [ $? -ne 0 ]; do
		echo "Package installation failed, retrying in 60s: $@"
		sleep 60
		sudo apt-get -qq install "$@" < /dev/null > /dev/null
	done
}


# Install dependencies from apt
apt-install openjdk-11-jdk postgresql postgresql-client


# Install gcloud if not already installed
gcloud --version > /dev/null
if [ $? -ne 0 ]; then
  # Copied from https://cloud.google.com/sdk/docs/downloads-apt-get
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
  apt-install apt-transport-https ca-certificates gnupg
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
  apt-install google-cloud-sdk
  gcloud services enable compute
fi


# Pull build artifacts
gsutil -m cp -r gs://bank-of-anthos/monolith /opt/


# Export application environment variables
source <(sed -E -n 's/[^#]+/export &/ p' /opt/monolith/${APP_ENV})


# Extract the public key and write it to a file
awk '/jwtRS256.key.pub/{print $2}' /opt/monolith/${JWT_SECRET} | base64 -d >> $PUB_KEY_PATH


# Start PostgreSQL
pg_ctlcluster 11 main start


# Configure PostgreSQL
sudo -u postgres psql --command "CREATE DATABASE $POSTGRES_DB;"
sudo -u postgres psql --command "CREATE USER $POSTGRES_USER;"
sudo -u postgres psql --command "ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"
sudo -u postgres psql --command "ALTER USER $POSTGRES_USER WITH SUPERUSER;"


# Init database with any included SQL scripts
sudo -u postgres psql -d $POSTGRES_DB -f /opt/monolith/initdb/*.sql


# Init database with any included bash scripts
export POSTGRES_USER=postgres  # Hack around PostgreSQL peer auth restrictions
for script in /opt/monolith/initdb/*.sh; do
  sudo --preserve-env=USE_DEMO_DATA,POSTGRES_DB,POSTGRES_USER,LOCAL_ROUTING_NUM -u postgres bash "$script" -H
done


# Start the ledgermonolith service
nohup java -jar /opt/monolith/${APP_JAR} > /var/log/monolith.log &


echo "Startup Complete"
exit

