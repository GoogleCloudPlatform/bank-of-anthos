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


# Boot script to install and start the ledgermonolith service from a JAR.
#
# Expects build artifacts to be available on Google Cloud Storage.
# The GCS bucket is set with instance custom metadata 'gcs-bucket'
#
# Designed to be attached as a startup script to a Google Compute Engine VM.

set -v


# Define names of expected build artifacts
APP_JAR=ledgermonolith.jar
APP_ENV=ledgermonolith.env
JWT_SECRET=jwt-secret.yaml
DB_INIT_DIR=initdb


# Define where to put monolith artifacts
MONOLITH_DIR=/opt/monolith
MONOLITH_LOG=/var/log/monolith.log
MONOLITH_SERVICE=ledgermonolith.service

# Check if already installed
if systemctl is-enabled ${MONOLITH_SERVICE} ; then
  echo "ledgermonolith-service has been already installed"
  exit 0
fi

# If not provided, get the Google Cloud Storage bucket to retrieve build artifacts from
if [ -z "${GCS_BUCKET}" ] ; then
  GCS_BUCKET=$(curl "http://metadata/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
fi
echo "GCS_BUCKET: $GCS_BUCKET"
GCS_PATH=${GCS_BUCKET}/monolith


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
mkdir $MONOLITH_DIR
gsutil -m cp -r gs://${GCS_PATH}/* ${MONOLITH_DIR}


# Export application environment variables
source <(sed -E -n 's/[^#]+/export &/ p' ${MONOLITH_DIR}/${APP_ENV})


# Extract the public key and write it to a file
awk '/jwtRS256.key.pub/{print $2}' ${MONOLITH_DIR}/${JWT_SECRET} | base64 -d > $PUB_KEY_PATH


# Start PostgreSQL
pg_ctlcluster 11 main start


# Configure PostgreSQL
sudo -u postgres psql --command "CREATE DATABASE ${POSTGRES_DB};"


# Init database with any included SQL scripts
sudo -u postgres psql -d $POSTGRES_DB -f ${MONOLITH_DIR}/${DB_INIT_DIR}/*.sql


# Init database with any included bash scripts
for script in ${MONOLITH_DIR}/${DB_INIT_DIR}/*.sh; do
  sudo --preserve-env=USE_DEMO_DATA,POSTGRES_DB,POSTGRES_USER,LOCAL_ROUTING_NUM -u postgres bash "${script}" -H
done


# Secure the database user with a password
sudo -u postgres psql --command "ALTER USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';"


# Setup ledgermonolith service
cat <<EOF >${MONOLITH_DIR}/ledgermonolith-service.sh
#!/bin/bash
source <(sed -E -n 's/[^#]+/export &/ p' ${MONOLITH_DIR}/${APP_ENV})
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

echo "Install Complete"
exit
