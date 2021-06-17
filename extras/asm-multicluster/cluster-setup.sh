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

#!/bin/bash 

# USES ASM 1.9 - SINGLE PROJECT - GOOGLE-MANAGED CONTROL PLANE 
# https://cloud.google.com/service-mesh/docs/gke-install-multi-cluster 

########### VARIABLES  ##################################
if [[ -z "$PROJECT_ID" ]]; then
    echo "Must provide PROJECT_ID in environment" 1>&2
    exit 1
fi

export CLUSTER_1_NAME="cluster-1"
export CLUSTER_1_ZONE="us-central1-a"

export CLUSTER_2_NAME="cluster-2"
export CLUSTER_2_ZONE="us-central1-b"
############################################################


# Note - workload identity is required for ASM 
echo "☸️ Creating clusters..."

gcloud config set project ${PROJECT_ID}
gcloud services enable container.googleapis.com

gcloud beta container clusters create ${CLUSTER_1_NAME} \
--project=${PROJECT_ID} --zone=${CLUSTER_1_ZONE} \
--release-channel=regular  --image-type cos_containerd \
--machine-type=e2-standard-4 --num-nodes=4 \
--workload-pool=${PROJECT_ID}.svc.id.goog --async 

gcloud beta container clusters create ${CLUSTER_2_NAME} \
--project=${PROJECT_ID} --zone=${CLUSTER_2_ZONE} \
--release-channel=regular  --image-type cos_containerd \
--machine-type=e2-standard-4 --num-nodes=4 \
--workload-pool=${PROJECT_ID}.svc.id.goog 


echo "💻 Setting local kubectx..."
gcloud container clusters get-credentials ${CLUSTER_1_NAME} --zone ${CLUSTER_1_ZONE} 
kubectx cluster-1=. 

gcloud container clusters get-credentials ${CLUSTER_2_NAME} --zone ${CLUSTER_2_ZONE} 
kubectx cluster-2=. 

echo "🔥 Adding a firewall rule for cross-cluster pod traffic..."
function join_by { local IFS="$1"; shift; echo "$*"; }

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

echo "⬇️ Installing required tools for ASM..."
# https://cloud.google.com/service-mesh/docs/scripted-install/asm-onboarding#installing_required_tools 
curl https://storage.googleapis.com/csm-artifacts/asm/install_asm_1.9 > install_asm
curl https://storage.googleapis.com/csm-artifacts/asm/install_asm_1.9.sha256 > install_asm.sha256
sha256sum -c --ignore-missing install_asm.sha256 
chmod +x install_asm

echo "🕸 Installing ASM on cluster-1..."
# https://cloud.google.com/service-mesh/docs/managed-control-plane 
kubectx cluster-1 

./install_asm --mode install --managed -p ${PROJECT_ID} \
    -l ${CLUSTER_1_ZONE} -n ${CLUSTER_1_NAME} -v \
    --output_dir asm-${CLUSTER_1_NAME} --enable-all 

# get "revision" from directory created by install_asm script 
for dir in asm-${CLUSTER_1_NAME}/istio-*/ ; do
    export REVISION=`basename $dir`
    echo "Revision is: $REVISION" 
done

echo "⛵️ Installing the Istio IngressGateway on cluster-1..."
./asm-${CLUSTER_1_NAME}/$REVISION/bin/istioctl install -f ./asm-${CLUSTER_1_NAME}/managed_control_plane_gateway.yaml --set revision=asm-managed -y

echo "🕸 Installing ASM on cluster-2..."
kubectx cluster-2 

./install_asm --mode install --managed -p ${PROJECT_ID} \
    -l ${CLUSTER_2_ZONE} -n ${CLUSTER_2_NAME} -v \
    --output_dir asm-${CLUSTER_2_NAME} --enable-all


echo "🌏 Setting up Endpoint Discovery between clusters..."
# https://cloud.google.com/service-mesh/docs/managed-control-plane#configure_endpoint_discovery_only_for_multi-cluster_installations 

export CTX_1="cluster-1"
export CTX_2="cluster-2"

export CLUSTER_1_FULL_NAME="gke_${PROJECT_ID}_${CLUSTER_1_ZONE}_${CLUSTER_1_NAME}"
export CLUSTER_2_FULL_NAME="gke_${PROJECT_ID}_${CLUSTER_2_ZONE}_${CLUSTER_2_NAME}"


echo "Letting cluster 1 know about cluster 2..."  
./asm-${CLUSTER_1_NAME}/$REVISION/bin/istioctl x create-remote-secret --context=${CTX_2} --name=${CLUSTER_2_FULL_NAME} | kubectl apply -f - --context=${CTX_1}

kubectx cluster-1 
kubectl get secret istio-remote-secret-cluster2 -n istio-system 

# Let cluster 2 know about cluster 1 
./asm-${CLUSTER_1_NAME}/$REVISION/bin/istioctl x create-remote-secret --context=${CTX_1} --name=${CLUSTER_1_FULL_NAME} | kubectl apply -f - --context=${CTX_2}

kubectx cluster-2 
kubectl get secret istio-remote-secret-cluster1 -n istio-system

echo "✏️ Labeling the default namespace for Istio injection..."
kubectx cluster-1 
kubectl label namespace default istio-injection- istio.io/rev=asm-managed --overwrite

kubectx cluster-2
kubectl label namespace default istio-injection- istio.io/rev=asm-managed --overwrite


echo "☁️ Setting up workload identity permissions for the app..."
export GSA_NAME="boa-gsa"
export KSA_NAME="default"
export NAMESPACE="default"

echo "🔐 Creating GCP and K8s service accounts..."
gcloud iam service-accounts create $GSA_NAME


echo "🔐  Annotating service accounts to connect your GSA and KSA..."
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[$NAMESPACE/$KSA_NAME]" \
  $GSA_NAME@$PROJECT_ID.iam.gserviceaccount.com

kubectl annotate serviceaccount \
  --namespace $NAMESPACE \
  $KSA_NAME \
  iam.gke.io/gcp-service-account=$GSA_NAME@$PROJECT_ID.iam.gserviceaccount.com


echo "🔐  Granting Service account permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/cloudtrace.agent

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/monitoring.metricWriter

echo "✅ Done setting up clusters."