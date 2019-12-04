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
    --cluster-version=1.13.11-gke.14 \
    --machine-type=n1-standard-2 --num-nodes=4 \
    --enable-stackdriver-kubernetes --subnetwork=default \
    --identity-namespace=${PROJECT}.svc.id.goog --labels csm=

# Install Istio
#curl -L https://git.io/getLatestIstio |  ISTIO_VERSION=1.3.0 sh -
#kubectl create namespace istio-system
#helm template istio-1.3.0/install/kubernetes/helm/istio-init \
#    --name istio-init --namespace istio-system | kubectl apply -f -
#kubectl -n istio-system wait --for=condition=complete job --all
#helm template istio-1.3.0/install/kubernetes/helm/istio \
#    --name istio --namespace istio-system | kubectl apply -f -
#kubectl create clusterrolebinding cluster-admin-binding \
#    --clusterrole="cluster-admin" --user=${ACCOUNT}
#gsutil cat gs://csm-artifacts/stackdriver/stackdriver.istio.csm_beta.yaml | \
#    sed 's@<mesh_uid>@'${PROJECT}/${ZONE}/${CLUSTER}@g | kubectl apply -f -

## enable ASM
#gcloud iam service-accounts create istio-mixer --display-name istio-mixer --project ${PROJECT} | true
#gcloud projects add-iam-policy-binding ${PROJECT} \
#    --member=serviceAccount:istio-mixer@${PROJECT}.iam.gserviceaccount.com \
#    --role=roles/contextgraph.asserter
#gcloud projects add-iam-policy-binding ${PROJECT} \
#    --member=serviceAccount:istio-mixer@${PROJECT}.iam.gserviceaccount.com \
#    --role=roles/logging.logWriter
#gcloud projects add-iam-policy-binding ${PROJECT} \
#    --member=serviceAccount:istio-mixer@${PROJECT}.iam.gserviceaccount.com \
#    --role=roles/monitoring.metricWriter
#gcloud iam service-accounts add-iam-policy-binding  \
#    --role roles/iam.workloadIdentityUser \
#    --member "serviceAccount:${PROJECT}.svc.id.goog[istio-system/istio-mixer-service-account]" istio-mixer@${PROJECT}.iam.gserviceaccount.com
#kubectl annotate serviceaccount \
#    --namespace istio-system istio-mixer-service-account iam.gke.io/gcp-service-account=istio-mixer@${PROJECT}.iam.gserviceaccount.com
## enable sidecars in default namespace
#kubectl label namespace default istio-injection=enabled
