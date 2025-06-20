#!/bin/bash

PROJECT_ID=$(gcloud config get-value project --format json | jq -r)
REGION="us-central1"
CLUSTER_NAME="komo-workshop-rbopcn9o" # Replace with your cluster name
NODE_SERVICE_ACCOUNT="tf-gke-komo-workshop-2-jfbg@${PROJECT_ID}.iam.gserviceaccount.com" # replace with your node service account
NODE_SERVICE_ACCOUNT=$(gcloud container clusters describe ${CLUSTER_NAME} \
  --region us-central1 \
  --format="value(nodeConfig.serviceAccount)")
K8S_NAMESPACE="default"
K8S_SERVICE_ACCOUNT="bank-of-anthos"
ARTIFACT_REGISTRY_REPO="bank-of-anthos"

# Enable Cloud Trace API
gcloud services enable cloudtrace.googleapis.com --project=$PROJECT_ID

# Grant Artifact Registry reader access to node service account
gcloud artifacts repositories add-iam-policy-binding $ARTIFACT_REGISTRY_REPO \
  --location=$REGION \
  --member="serviceAccount:${NODE_SERVICE_ACCOUNT}" \
  --role="roles/artifactregistry.reader"

# Grant Cloud Trace access to node service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${NODE_SERVICE_ACCOUNT}" \
  --role="roles/cloudtrace.agent"

# Enable Workload Identity binding to the Kubernetes service account
gcloud iam service-accounts add-iam-policy-binding \
  ${NODE_SERVICE_ACCOUNT} \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${K8S_SERVICE_ACCOUNT}]"

echo "Node Service Account is ${NODE_SERVICE_ACCOUNT}"

# Grant Service Account Token Creator permissions to node's service account
gcloud iam service-accounts add-iam-policy-binding ${NODE_SERVICE_ACCOUNT} \
  --role roles/iam.serviceAccountTokenCreator \
  --member="serviceAccount:${NODE_SERVICE_ACCOUNT}"


gcloud iam service-accounts add-iam-policy-binding ${NODE_SERVICE_ACCOUNT} \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${K8S_SERVICE_ACCOUNT}]"

# Annotate Kubernetes service account for Workload Identity
kubectl annotate serviceaccount ${K8S_SERVICE_ACCOUNT} \
  --namespace ${K8S_NAMESPACE} \
  iam.gke.io/gcp-service-account=${NODE_SERVICE_ACCOUNT} \
  --overwrite

kubectl annotate serviceaccount bank-of-anthos \
  iam.gke.io/gcp-service-account=774432512437-compute@developer.gserviceaccount.com \
  --overwrite

# Restart deployments to apply changes
kubectl rollout restart deployment --namespace ${K8S_NAMESPACE}