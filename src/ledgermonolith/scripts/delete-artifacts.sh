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

# Script to delete build artifacts on GCS for the ledgermonolith service


# Google Cloud Storage bucket to delete build artifacts from
if [[ -z ${GCS_BUCKET} ]]; then
  echo "GCS_BUCKET must be set"
  exit 0
else
  echo "GCS_BUCKET: ${GCS_BUCKET}"
fi
GCS_PATH=${GCS_BUCKET}/monolith


# Delete the artifacts in GCS
gcloud storage rm --recursive gs://${GCS_PATH}
echo "Deleted $GCS_PATH from Google Cloud Storage"
