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

# Boot script to install and start the ledgermonolith service and/or database.
#
# Expects build artifacts to be available on Google Cloud Storage.
# - The GCS bucket can be overriden by setting the instance custom
#   metadata 'gcs-bucket'
# - The environment configuration can be overriden by setting the instance
#   custom metadata 'env-config'
# - The components to be installed can be overriden by setting the instance
#   custom metadata 'install-component'
#
# Designed to be attached as a startup script to a Google Compute Engine VM.

set -v -x

# Function to install packages from apt and retry if needed
function apt-install() {
  apt-get -qq install "${@}" </dev/null >/dev/null
  while [ ${?} -ne 0 ]; do
    echo "Package installation failed, retrying in 60s: ${@}"
    sleep 60
    apt-get -qq install "${@}" </dev/null >/dev/null
  done
}

function install_database() {
  echo "Start Database Install"

  # Check if already installed
  if systemctl is-enabled postgresql; then
    echo "postgresql has been already installed"
    return
  fi

  # Install dependencies from apt
  apt-install postgresql-${POSTGRES_VERSION}

  if [[ ${COMPONENT,,} == "database" ]]; then
    # Configure PostgreSQL to listen on all interfaces
    POSTGRESQL_CONF_FILE=${POSTGRESQL_CONF:-/etc/postgresql/${POSTGRES_VERSION}/main/postgresql.conf}
    sed -i "/#listen_addresses =/c\listen_addresses = '*'                  # what IP address(es) to listen on;" ${POSTGRESQL_CONF_FILE}
    POSTGRESQL_HBA_CONF_FILE=${POSTGRESQL_HBA_CONF_FILE:-/etc/postgresql/${POSTGRES_VERSION}/main/pg_hba.conf}
    echo "host    all             all             0.0.0.0/0               password" >>${POSTGRESQL_HBA_CONF_FILE}
  fi

  # Start PostgreSQL
  pg_ctlcluster ${POSTGRES_VERSION} main start

  # Configure PostgreSQL
  sudo -u postgres psql --command "CREATE DATABASE ${POSTGRES_DB};"

  # Init database with any included SQL scripts
  sudo -u postgres psql -d ${POSTGRES_DB} -f ${MONOLITH_DIR}/${DB_INIT_DIR}/*.sql

  # Init database with any included bash scripts
  for script in ${MONOLITH_DIR}/${DB_INIT_DIR}/*.sh; do
    sudo --preserve-env=USE_DEMO_DATA,POSTGRES_DB,POSTGRES_PASSWORD,POSTGRES_USER,LOCAL_ROUTING_NUM -u postgres bash "${script}" -H
  done

  # Secure the database user with a password
  sudo -u postgres psql --command "ALTER USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"

  echo "Database Install Complete"

  if [[ ${COMPONENT,,} == "database" ]]; then
    # Reboot to pick up listen_addresses changes
    reboot now
  fi
}

function install_service() {
  echo "Start Service Install"

  # Check if already installed
  if systemctl is-enabled ${MONOLITH_SERVICE}; then
    echo "ledgermonolith-service has been already installed"
    return
  fi

  # Install Java 17
  wget --no-verbose https://download.java.net/java/GA/jdk17.0.1/2a2082e5a09d4267845be086888add4f/12/GPL/openjdk-17.0.1_linux-x64_bin.tar.gz
  tar xf openjdk-*.tar.gz -C /opt

  # Install gcloud if not already installed
  gcloud --version >/dev/null
  if [ ${?} -ne 0 ]; then
    # Copied from https://cloud.google.com/sdk/docs/downloads-apt-get
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" >>/etc/apt/sources.list.d/google-cloud-sdk.list
    apt-install apt-transport-https ca-certificates gnupg
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    apt-install google-cloud-sdk
    gcloud services enable compute
  fi

  # Extract the public key and write it to a file
  awk '/jwtRS256.key.pub/{print $2}' ${MONOLITH_DIR}/${JWT_SECRET} | base64 -d >${PUB_KEY_PATH}

  # Setup ledgermonolith service
  cat <<EOF >${MONOLITH_DIR}/ledgermonolith-service.sh
#!/bin/bash
source <(sed -E -n 's/[^#]+/export &/ p' ${MONOLITH_DIR}/${APP_ENV})
export JAVA_HOME=/opt/jdk-17.0.1
export PATH=\$JAVA_HOME/bin:\$PATH
java -jar ${MONOLITH_DIR}/${APP_JAR} > ${MONOLITH_LOG}
EOF
  chmod +x ${MONOLITH_DIR}/ledgermonolith-service.sh

  cat <<EOF >/etc/systemd/system/${MONOLITH_SERVICE}
[Service]
Type=simple
RemainAfterExit=yes
ExecStart=${MONOLITH_DIR}/ledgermonolith-service.sh

[Install]
WantedBy=multi-user.target
EOF

  systemctl enable ${MONOLITH_SERVICE}
  systemctl start ${MONOLITH_SERVICE}

  echo "Service Install Complete"
}

#
# MAIN
########################################################################################

# Define names of expected build artifacts
APP_JAR=ledgermonolith.jar
APP_ENV=ledgermonolith.env
JWT_SECRET=jwt-secret.yaml
DB_INIT_DIR=initdb

# Define where to put monolith artifacts
MONOLITH_DIR=/opt/monolith
MONOLITH_LOG=/var/log/monolith.log
MONOLITH_SERVICE=ledgermonolith.service

# Query the Metadata Service for the build artifacts Google Cloud Storage bucket
GCS_METADATA_VALUE=$(curl --fail --show-error --silent "http://metadata/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
if [ ${?} == 0 ]; then
  GCS_BUCKET=${GCS_METADATA_VALUE}
fi

# If no value was found, default to bank-of-anthos-ci
GCS_BUCKET=${GCS_BUCKET:-bank-of-anthos-ci}

echo "GCS_BUCKET: ${GCS_BUCKET}"
GCS_PATH=${GCS_BUCKET}/monolith

mkdir -p ${MONOLITH_DIR}

# Pull build artifacts
gcloud storage cp --recursive gs://${GCS_PATH}/* ${MONOLITH_DIR}

# Query the Metadata Service for the environment config
# If no value was found, use the default configuration from the storage bucket
ENV_METADATA_VALUE=$(curl --fail --show-error --silent "http://metadata/computeMetadata/v1/instance/attributes/env-config" -H "Metadata-Flavor: Google")
if [ ${?} == 0 ]; then
  cat <<EOF >${MONOLITH_DIR}/${APP_ENV}
${ENV_METADATA_VALUE}
EOF
fi

# Export application environment variables
source <(sed -E -n 's/[^#]+/export &/ p' ${MONOLITH_DIR}/${APP_ENV})

# Add postgresql.org repo
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Update apt packages and retry if needed
apt-get -qq update </dev/null >/dev/null
while [ ${?} -ne 0 ]; do
  sleep 60
  apt-get -qq update </dev/null >/dev/null
done

# Install common dependencies from apt
POSTGRES_VERSION=${POSTGRES_VERSION:-14}
apt-install postgresql-client-${POSTGRES_VERSION} wget

COMPONENT_METADATA_VALUE=$(curl --fail --show-error --silent "http://metadata/computeMetadata/v1/instance/attributes/install-component" -H "Metadata-Flavor: Google")
if [ ${?} == 0 ]; then
  COMPONENT=${COMPONENT_METADATA_VALUE}
fi
COMPONENT=${COMPONENT:-""}

if [[ ${COMPONENT,,} == "database" ]]; then
  install_database
elif [[ ${COMPONENT,,} == "service" ]]; then
  install_service
else
  install_database
  install_service
fi

exit
