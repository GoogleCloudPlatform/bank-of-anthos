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

APP_JAR=ledgermonolith.jar

# If the GCS bucket doesn't exist, then create it and upload required files
gsutil ls gs://bank-of-anthos/monolith &> /dev/null
if [ $? -ne 0 ]; then
  gsutil mb -p $PROJECT_ID gs://bank-of-anthos/monolith

  # Push jar
  gsutil cp $CWD/target/ledgermonolith-1.0.jar gs://bank-of-anthos/monolith/${APP_JAR}

  # Push ledger-db init scripts
  gsutil cp $CWD/ledger-db/initdb/tables.sql gs://bank-of-anthos/monolith/tables.sql
  gsutil cp $CWD/ledger-db/initdb/data.sql gs://bank-of-anthos/monolith/data.sql
fi

