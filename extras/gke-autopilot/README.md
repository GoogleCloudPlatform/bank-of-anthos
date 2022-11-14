# StatefulSet worload with HPA

Run command in GCP CloudShell env [![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://ide.cloud.google.com?cloudshell_git_repo=https://github.com/GoogleCloudPlatform/bank-of-anthos.git&cloudshell_git_branch=main&cloudshell_workspace=&cloudshell_tutorial=TUTORIAL.md&show=terminal&ephemeral=false
)

## Prerequisites

Create GKE Autopilot. Change `REGION` or `GKE_NAME` to your values if you like.

```bash
REGION="us-central1"
GKE_NAME="bank-of-anthos"
gcloud container clusters create-auto "$GKE_NAME" --region="$REGION"
```

Execution of these commands take some time.

If needed obtain access to GKE

```bash
gcloud container clusters get-credentials "$GKE_NAME" --region="$REGION"
```

## Setup Service Accounts with Workload Identity

```bash
GSA_NAME="bank-of-anthos"
GSA_EMAIL="$GSA_NAME@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com"

gcloud iam service-accounts create "$GSA_NAME"

gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" \
    --member "serviceAccount:$GSA_EMAIL" \
    --role roles/cloudtrace.agent

gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" \
    --member "serviceAccount:$GSA_EMAIL" \
    --role roles/monitoring.metricWriter

gcloud iam service-accounts add-iam-policy-binding "$GSA_EMAIL" \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$GOOGLE_CLOUD_PROJECT.svc.id.goog[default/default]"

kubectl annotate serviceaccount "default" \
    "iam.gke.io/gcp-service-account=$GSA_EMAIL"
```

> Note: this tutorial assumes deployment to the cluster `default` namespace.

## Deploy Custom Metrics Adapter

Use legacy model because of `prometheus-to-sd` tool used in postgresql helm chart configuration.

```bash
gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" \
    --member "serviceAccount:$GSA_EMAIL" \
    --role roles/monitoring.viewer

gcloud iam service-accounts add-iam-policy-binding \
    "$GSA_EMAIL" \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$GOOGLE_CLOUD_PROJECT.svc.id.goog[custom-metrics/custom-metrics-stackdriver-adapter]"

kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/k8s-stackdriver/master/custom-metrics-stackdriver-adapter/deploy/production/adapter.yaml

kubectl annotate serviceaccount -n custom-metrics "custom-metrics-stackdriver-adapter" \
    "iam.gke.io/gcp-service-account=$GSA_EMAIL"
```

Restart custom metrics adapter pod if you see errors related to permissions (403)

## Clone Bank of Anthos

```bash
git clone https://github.com/GoogleCloudPlatform/bank-of-anthos.git
cd bank-of-anthos/
```

## ConfigMap for database init scripts

```bash
kubectl create configmap initdb \
  --from-file=src/accounts-db/initdb/0-accounts-schema.sql \
  --from-file=src/accounts-db/initdb/1-load-testdata.sql
```

## Deploy Postgresql with helm

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install accounts-db bitnami/postgresql-ha \
  --version 10.0.1 \
  --values extras/gke-autopilot/helm-postgres-ha/values.yaml \
  --set="postgresql.initdbScriptsCM=initdb" \
  --set="postgresql.replicaCount=1" \
  --wait
```

## Deploy Bank of Anthos

```bash
kubectl apply -f extras/jwt/jwt-secret.yaml
kubectl apply -f extras/gke-autopilot/kubernetes-manifests
```

Wait until Bank of Anthos application will up and running.

## Configure HPA

This exercise will show you how to enable horizontal pod autoscaling in response to HTTP requests increase

### Prepare HPA for Frontend service

Discover an exact name of frontend’s ingress LoadBalancer using the following command:

```bash
FW_RULE=$(kubectl get ingress frontend -o=jsonpath='{.metadata.annotations.ingress\.kubernetes\.io/forwarding-rule}')
echo $FW_RULE
sed -i "s/FORWARDING_RULE_NAME/$FW_RULE/g" "extras/gke-autopilot/hpa/frontend.yaml"
```

### Deploy HPA

```bash
kubectl apply -f extras/gke-autopilot/hpa
```

## Deploy loadgenerator

Wait when application will be available on IP address of load balancer and start this process.

```bash
LB_IP=$(kubectl get ingress frontend -o=jsonpath='{ .status.loadBalancer.ingress[0].ip}')
echo $LB_IP
sed -i "s/FRONTEND_IP_ADDRESS/$LB_IP/g" "extras/gke-autopilot/loadgenerator.yaml"
```

Apply kubernetes deployment manifest

```bash
kubectl apply -f extras/gke-autopilot/loadgenerator.yaml
kubectl port-forward "svc/loadgenerator" 8080
```

Click on `Web Preview` button and select `Preview on port 8080`. This will open a new tab in browser with locust UI.
The load generator has auto-start enabled by default. You should be able to observe it's execution

## Clean up

```bash
kubectl delete \
    -f extras/gke-autopilot/loadgenerator.yaml \
    -f extras/gke-autopilot/hpa \
    -f extras/gke-autopilot/kubernetes-manifests \
    -f https://raw.githubusercontent.com/GoogleCloudPlatform/k8s-stackdriver/master/custom-metrics-stackdriver-adapter/deploy/production/adapter.yaml
helm uninstall accounts-db
kubectl delete pvc -l "app.kubernetes.io/instance=accounts-db"

# Cleanup GSA
gcloud container clusters delete "$GKE_NAME" --region="$REGION" --quiet
gcloud projects remove-iam-policy-binding \
    $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$GSA_EMAIL" \
    --role="roles/cloudtrace.agent"
gcloud projects remove-iam-policy-binding \
    $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$GSA_EMAIL" \
    --role="roles/monitoring.metricWriter"
gcloud projects remove-iam-policy-binding \
    $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:$GSA_EMAIL" \
    --role="roles/monitoring.viewer"
gcloud iam service-accounts delete "$GSA_EMAIL" --quiet
```
