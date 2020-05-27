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
DB_TABLES=tables.sql
JWT_SECRET=jwt-secret.yaml


# Set required environment variables
export VERSION="v0.1.0"
export PORT="8080"
export JVM_OPTS="-XX:+UnlockExperimentalVMOptions -XX:+UseCGroupMemoryLimitForHeap"
export LOCAL_ROUTING_NUM="123456789"
export PUB_KEY_PATH="/opt/ledgermonolith/publickey"
export BALANCES_API_ADDR="127.0.0.1:8080"
export POSTGRES_DB="postgresdb"
export POSTGRES_USER="admin"
export POSTGRES_PASSWORD="password"
export SPRING_DATASOURCE_URL="jdbc:postgresql://ledger-db:5432/postgresdb"
export SPRING_DATASOURCE_USERNAME="admin" # should match POSTGRES_USER
export SPRING_DATASOURCE_PASSWORD="password" # should match POSTGRES_PASSWORD


# Talk to the metadata server to get the project id
PROJECTID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
echo "Project ID: ${PROJECTID}"


# Install dependencies from apt
apt-get update; apt-get install -yq openjdk-11-jdk postgresql-12 postgresql-client


# Install gcloud if not already installed
gcloud --version
if [ $? -ne 0 ]; then
  # Copied from https://cloud.google.com/sdk/docs/downloads-apt-get
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
  sudo apt-get install apt-transport-https ca-certificates gnupg
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
  sudo apt-get update && sudo apt-get install google-cloud-sdk
  gcloud services enable compute
fi


# TODO: figure out permissions to access these buckets
# Pull build artifacts
mkdir /opt/ledgermonolith
gsutil cp gs://bank-of-anthos/monolith/${APP_JAR} /opt/ledgermonolith/${APP_JAR}
gsutil cp gs://bank-of-anthos/monolith/${DB_TABLES} /opt/ledgermonolith/${DB_TABLES}
gsutil cp gs://bank-of-anthos/monolith/${JWT_SECRET} /opt/ledgermonolith/${JWT_SECRET}


# Helper function to read JWT public key from jwt-secret.yaml
function yaml() {
  hashdot=$(gem list hash_dot);
  if ! [ "$hashdot" != "" ]; then sudo gem install "hash_dot" ; fi
  if [ -f $1 ];then
    cmd=" Hash.use_dot_syntax = true; hash = YAML.load(File.read('$1'));";
    if [ "$2" != "" ] ;then 
      cmd="$cmd puts hash.$2;"
    else
      cmd="$cmd puts hash;"
    fi
    ruby  -r yaml -r hash_dot <<< $cmd;
  fi
}


# Extract the public key and write it to a file
echo $(yaml /opt/ledgermonolith/${JWT_SECRET} data.jwtRS256.key.pub) > /opt/ledgermonolith/publickey


# Start postgres under user 'postgres'
pg_ctl start -D /usr/local/pgsql/data -l serverlog &


# Init ledger-db database with SQL scripts
psql postgres -h 127.0.0.1 -d $POSTGRES_DB -f /opt/ledgermonolith/${DB_TABLES}


# Start the ledgermonolith application under user 'monolith'
java -jar /opt/ledgermonolith/${APP_JAR} &


echo "Startup Complete"
exit

