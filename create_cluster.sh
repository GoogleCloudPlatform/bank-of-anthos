#!/bin/bash

if [ "$1" != ""   ]; then
    PROJECT="$1"
else
    echo "project not set"
    exit 1
fi
if [ "$2" != ""  ]; then
    CLUSTER="$2"
else
    CLUSTER="seattle"
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
    --cluster-version=1.13.11-gke.9 \
    --machine-type=n1-standard-2 --num-nodes=4 \
    --enable-stackdriver-kubernetes --subnetwork=default \
    --identity-namespace=${PROJECT}.svc.id.goog --labels csm=

# Install Istio
curl -L https://git.io/getLatestIstio |  ISTIO_VERSION=1.3.0 sh -
kubectl create namespace istio-system
helm template istio-1.3.0/install/kubernetes/helm/istio-init \
    --name istio-init --namespace istio-system | kubectl apply -f -
kubectl -n istio-system wait --for=condition=complete job --all
helm template istio-1.3.0/install/kubernetes/helm/istio \
    --name istio --namespace istio-system | kubectl apply -f -
kubectl create clusterrolebinding cluster-admin-binding \
    --clusterrole="cluster-admin" --user=${ACCOUNT}
gsutil cat gs://csm-artifacts/stackdriver/stackdriver.istio.csm_beta.yaml | \
    sed 's@<mesh_uid>@'${PROJECT}/${ZONE}/${CLUSTER}@g | kubectl apply -f -

# enable ASM
gcloud iam service-accounts create istio-mixer --display-name istio-mixer --project ${PROJECT} | true
gcloud projects add-iam-policy-binding ${PROJECT} \
    --member=serviceAccount:istio-mixer@${PROJECT}.iam.gserviceaccount.com \
    --role=roles/contextgraph.asserter
gcloud projects add-iam-policy-binding ${PROJECT} \
    --member=serviceAccount:istio-mixer@${PROJECT}.iam.gserviceaccount.com \
    --role=roles/logging.logWriter
gcloud projects add-iam-policy-binding ${PROJECT} \
    --member=serviceAccount:istio-mixer@${PROJECT}.iam.gserviceaccount.com \
    --role=roles/monitoring.metricWriter
gcloud iam service-accounts add-iam-policy-binding  \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:${PROJECT}.svc.id.goog[istio-system/istio-mixer-service-account]" istio-mixer@${PROJECT}.iam.gserviceaccount.com
kubectl annotate serviceaccount \
    --namespace istio-system istio-mixer-service-account iam.gke.io/gcp-service-account=istio-mixer@${PROJECT}.iam.gserviceaccount.com
# enable sidecars in default namespace
kubectl label namespace default istio-injection=enabled

kubectl create configmap branch-info \
    --from-literal branch_id=$CLUSTER \
    --from-literal key_version=1 \
    --from-literal keyring="projects/$PROJECT/locations/global/keyRings/$KEYRING_NAME"

#########################################################################
# KMS
#########################################################################

gcloud kms keyrings create $KEYRING_NAME  --location global --project $PROJECT

# create key for this cluster
gcloud kms keys create $CLUSTER \
  --location global \
  --keyring $KEYRING_NAME \
  --purpose asymmetric-signing \
  --default-algorithm ec-sign-p256-sha256 \
  --protection-level software \
  --project $PROJECT

# create a universal viewer service account
# create gcp sa
gcloud iam service-accounts create universal-key-viewer \
    --description "view public keys for all banks" \
    --display-name "universal-key-viewer" \
    --project $PROJECT
gcloud kms keys add-iam-policy-binding \
    $CLUSTER --location global --keyring $KEYRING_NAME \
    --member serviceAccount:universal-key-viewer@$PROJECT.iam.gserviceaccount.com \
    --role roles/cloudkms.publicKeyViewer \
    --project $PROJECT
# set up k8s sa with workload identity
kubectl create serviceaccount --namespace $K8S_NAMESPACE key-viewer
gcloud iam service-accounts add-iam-policy-binding \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT.svc.id.goog[$K8S_NAMESPACE/key-viewer]" \
    universal-key-viewer@$PROJECT.iam.gserviceaccount.com
kubectl annotate serviceaccount \
    --namespace $K8S_NAMESPACE \
    key-viewer \
    iam.gke.io/gcp-service-account=universal-key-viewer@$PROJECT.iam.gserviceaccount.com

# create a bank specific key signer
# create gcp sa
gcloud iam service-accounts create $CLUSTER-key-signer \
    --description "sign messages for $CLUSTER" \
    --display-name "$CLUSTER-key-signer" \
    --project $PROJECT
gcloud kms keys add-iam-policy-binding \
    $CLUSTER --location global --keyring $KEYRING_NAME \
    --member serviceAccount:$CLUSTER-key-signer@$PROJECT.iam.gserviceaccount.com \
    --role roles/cloudkms.signerVerifier \
    --project $PROJECT
# set up k8s sa with workload identity
kubectl create serviceaccount --namespace $K8S_NAMESPACE key-signer
gcloud iam service-accounts add-iam-policy-binding \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT.svc.id.goog[$K8S_NAMESPACE/key-signer]" \
    $CLUSTER-key-signer@$PROJECT.iam.gserviceaccount.com
kubectl annotate serviceaccount \
    --namespace $K8S_NAMESPACE \
    key-signer \
    iam.gke.io/gcp-service-account=$CLUSTER-key-signer@$PROJECT.iam.gserviceaccount.com
