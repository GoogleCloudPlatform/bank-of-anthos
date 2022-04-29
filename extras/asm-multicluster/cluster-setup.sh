#!/bin/bash
# Copyright 2021 Google LLC
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

# [START servicemesh_asm_multicluster_cluster_setup]

# USES ASM 1.9 - SINGLE PROJECT - GOOGLE-MANAGED CONTROL PLANE
# https://cloud.google.com/service-mesh/docs/gke-install-multi-cluster

########### VARIABLES  ##################################
if [[ -z "${PROJECT_ID}" ]]; then
  echo "Must set PROJECT_ID environment variable" 1>&2
  exit 1
fi

export CLUSTER_1_NAME="cluster-1"
export CLUSTER_1_ZONE="us-central1-a"

export CLUSTER_2_NAME="cluster-2"
export CLUSTER_2_ZONE="us-central1-b"
############################################################

echo "🔨 Checking required tools..."
kubectx=$(which kubectx)
if [ -z ${kubectx} ]; then
  kubectx=$(which kubectl-ctx)
  if [ -z ${kubectx} ]; then
    echo "kubectx isn't installed, exiting!"
    exit 1
  fi
fi

echo "☸️ Creating clusters..."
gcloud config set project ${PROJECT_ID}
gcloud services enable \
  container.googleapis.com \
  gkehub.googleapis.com

gcloud container clusters create ${CLUSTER_1_NAME} \
  --async \
  --project=${PROJECT_ID} \
  --zone=${CLUSTER_1_ZONE} \
  --release-channel=regular \
  --image-type cos_containerd \
  --machine-type=e2-standard-4 \
  --num-nodes=4 \
  --workload-pool=${PROJECT_ID}.svc.id.goog

gcloud container clusters create ${CLUSTER_2_NAME} \
  --async \
  --project=${PROJECT_ID} \
  --zone=${CLUSTER_2_ZONE} \
  --release-channel=regular \
  --image-type cos_containerd \
  --machine-type=e2-standard-4 \
  --num-nodes=4 \
  --workload-pool=${PROJECT_ID}.svc.id.goog

echo "☸️ Waiting for clusters to be created..."
while [[ 
  $(gcloud container clusters list \
    --project=${PROJECT_ID} \
    --filter="status!=RUNNING" 2>/dev/null | wc -l) != "0" ]]; do
  sleep 5
done

echo "💻 Setting local kubectx..."
gcloud container clusters get-credentials ${CLUSTER_1_NAME} --zone ${CLUSTER_1_ZONE}
${kubectx} cluster-1=.

gcloud container clusters get-credentials ${CLUSTER_2_NAME} --zone ${CLUSTER_2_ZONE}
${kubectx} cluster-2=.

echo "🔥 Adding a firewall rule for cross-cluster pod traffic..."
function join_by {
  local IFS="$1"
  shift
  echo "$*"
}

ALL_CLUSTER_CIDRS=$(gcloud container clusters list --format='value(clusterIpv4Cidr)' | sort | uniq)
ALL_CLUSTER_CIDRS=$(join_by , $(echo "${ALL_CLUSTER_CIDRS}"))
ALL_CLUSTER_NETTAGS=$(gcloud compute instances list --format='value(tags.items.[0])' | sort | uniq)
ALL_CLUSTER_NETTAGS=$(join_by , $(echo "${ALL_CLUSTER_NETTAGS}"))

gcloud compute firewall-rules create istio-multicluster-test-pods \
  --allow=tcp,udp,icmp,esp,ah,sctp \
  --direction=INGRESS \
  --priority=900 \
  --source-ranges="${ALL_CLUSTER_CIDRS}" \
  --target-tags="${ALL_CLUSTER_NETTAGS}" --quiet

ASMCLI_BINARY="./asmcli"
ASMCLI_BINARY_SHA="./asmcli.sha256 "

echo "⬇️ Installing the ASM installation tool..."
# https://cloud.google.com/service-mesh/docs/managed/configure-managed-anthos-service-mesh#download_the_installation_tool
curl \
  --location \
  --output ${ASMCLI_BINARY} \
  --show-error \
  --silent \
  https://storage.googleapis.com/csm-artifacts/asm/asmcli

curl \
  --location \
  --output ${ASMCLI_BINARY_SHA} \
  --show-error \
  --silent https://storage.googleapis.com/csm-artifacts/asm/asmcli.sha256

sha256sum -c --ignore-missing ${ASMCLI_BINARY_SHA}
chmod +x ${ASMCLI_BINARY}

echo "🕸 Installing ASM on cluster-1..."
# https://cloud.google.com/service-mesh/docs/managed/configure-managed-anthos-service-mesh#apply_the_google-managed_control_plane
${kubectx} cluster-1

${ASMCLI_BINARY} install \
  --channel regular \
  --cluster_location ${CLUSTER_1_ZONE} \
  --cluster_name ${CLUSTER_1_NAME} \
  --enable-all \
  --fleet_id ${PROJECT_ID} \
  --managed \
  --output_dir asm-${CLUSTER_1_NAME} \
  --project_id ${PROJECT_ID} \
  --verbose

# get "revision" from directory created by install_asm script
for dir in asm-${CLUSTER_1_NAME}/istio-*/; do
  export REVISION=$(basename $dir)
  echo "Revision is: ${REVISION}"
done

echo "⛵️ Installing the Istio IngressGateway on cluster-1..."
export GATEWAY_NAMESPACE="asm-ingress"
kubectl create namespace ${GATEWAY_NAMESPACE}
kubectl label namespace ${GATEWAY_NAMESPACE} istio-injection- istio.io/rev=asm-managed --overwrite
kubectl -n ${GATEWAY_NAMESPACE} apply -f ./asm-${CLUSTER_1_NAME}/samples/gateways/istio-ingressgateway

echo "🕸 Installing ASM on cluster-2..."
${kubectx} cluster-2

${ASMCLI_BINARY} install \
  --channel regular \
  --cluster_location ${CLUSTER_2_ZONE} \
  --cluster_name ${CLUSTER_2_NAME} \
  --enable-all \
  --fleet_id ${PROJECT_ID} \
  --managed \
  --output_dir asm-${CLUSTER_2_NAME} \
  --project_id ${PROJECT_ID} \
  --verbose

echo "🌏 Setting up Endpoint Discovery between clusters..."
# https://cloud.google.com/service-mesh/docs/unified-install/gke-install-multi-cluster#configure_endpoint_discovery_between_clusters

export CTX_1="cluster-1"
export CTX_2="cluster-2"

export CLUSTER_1_FULL_NAME="gke_${PROJECT_ID}_${CLUSTER_1_ZONE}_${CLUSTER_1_NAME}"
export CLUSTER_2_FULL_NAME="gke_${PROJECT_ID}_${CLUSTER_2_ZONE}_${CLUSTER_2_NAME}"

${ASMCLI_BINARY} create-mesh \
  ${PROJECT_ID} \
  ${PROJECT_ID}/${CLUSTER_1_ZONE}/${CLUSTER_1_NAME} \
  ${PROJECT_ID}/${CLUSTER_2_ZONE}/${CLUSTER_2_NAME}

echo "✏️ Labeling the default namespace for Istio injection..."
export GSA_NAME="boa-gsa"
export KSA_NAME="default"
export NAMESPACE="default"

${kubectx} cluster-1
kubectl label namespace ${NAMESPACE} istio-injection- istio.io/rev=asm-managed --overwrite

${kubectx} cluster-2
kubectl label namespace ${NAMESPACE} istio-injection- istio.io/rev=asm-managed --overwrite

echo "☁️ Setting up workload identity permissions for the app..."

echo "🔐 Creating GCP and K8s service accounts..."
gcloud iam service-accounts create ${GSA_NAME}

echo "🔐  Annotating service accounts to connect your GSA and KSA..."
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/${KSA_NAME}]" \
  ${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

kubectl annotate serviceaccount \
  --namespace ${NAMESPACE} \
  ${KSA_NAME} \
  iam.gke.io/gcp-service-account=${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

echo "🔐  Granting Service account permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/cloudtrace.agent

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/monitoring.metricWriter

echo "✅ Done setting up clusters."
# [END servicemesh_asm_multicluster_cluster_setup]
