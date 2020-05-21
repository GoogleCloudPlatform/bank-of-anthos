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

set -e
set -v

APP_JAR=ledgermonolith.jar

# Talk to the metadata server to get the project id
PROJECTID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")

echo "Project ID: ${PROJECTID}"

# Install dependencies from apt
apt-get install -yq openjdk-11-jdk git maven

mvn --version

mkdir /opt/ledgermonolith
gsutil cp gs://bank-of-anthos/${APP_JAR} /opt/ledgermonolith/${APP_JAR}
java -jar /opt/ledgermonolith/${APP_JAR} &

echo "Startup Complete"
exit

