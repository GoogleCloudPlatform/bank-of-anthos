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
  GCS_BUCKET=${PROJECT_ID}.bank-of-anthos-monolith
  echo "No GCS_BUCKET specified, using default: ${GCS_BUCKET}"
else
  echo "GCS_BUCKET: ${GCS_BUCKET}"
fi


# Delete the GCS bucket
gsutil -m rm -r gs://${GCS_BUCKET}
echo "Deleted bucket $GCS_BUCKET from Google Cloud Storage"
