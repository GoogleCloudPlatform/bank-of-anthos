#!/bin/bash
# Copyright 2019 Google LLC
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


if [ "$1" != ""   ]; then
    PROJECT="$1"
else
    echo "project not set"
    exit 1
fi
if [ "$2" != ""  ]; then
    CLUSTER="$2"
else
    CLUSTER="financial-demo"
fi
if [ "$3" != ""   ]; then
    ZONE="$3"
else
    ZONE="us-central1-a"
fi

KEYRING_NAME=bank-keys
K8S_NAMESPACE=default
ACCOUNT=$(gcloud config get-value account)

echo "creating cluster $CLUSTER in $ZONE under $PROJECT"

cd $(dirname $0)

# Create Cluster
gcloud beta container clusters create ${CLUSTER} \
    --project=${PROJECT} --zone=${ZONE} \
    --machine-type=n1-standard-2 --num-nodes=4 \
    --enable-stackdriver-kubernetes --subnetwork=default \
    --labels csm=
