# Backup for GKE

This directory contains files essential to demonstrate Backup for GKE service functionality.

For example to migrate from GKE Standart to GKE Autopilot cluster in other region.

## Steps

1. Create GKE Standard as Source cluster

  ```bash
  gcloud beta container clusters create "source-cluster" \
    --region="us-central1" \
    --addons="BackupRestore,HttpLoadBalancing"
  ```

1. Create GKE Autopilot as Destination cluster

  ```bash
  gcloud beta container clusters create-auto "destination-cluster" \
    --region="us-east1"
  ```

1. Enable Backup for GKE in Destination cluster

  ```bash
  gcloud container clusters update "${GKE_AUTOPILOT}" \
    --region="us-east1" \
    --update-addons="BackupRestore=ENABLED"
  ```

1. Create External Global IP

  ```bash
  gcloud compute addresses create "bank-of-anthos" --global
  ```

1. Deploy the Bank of Anthos to Source cluster

  ```bash
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" apply -f extras/jwt
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" apply -f kubernetes-manifests/
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" delete statefulset accounts-db ledger-db
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" apply -f extras/backup/kubernetes-manifests/
  ```

1. Access BoA and populate some data

1. Prepare for backup. Shutdown databases to avoid write operations

  ```bash
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" scale statefulset accounts-db --replicas 0
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" scale statefulset ledger-db --replicas 0
  ```

1. Create a backup plan

  ```bash
  gcloud beta container backup-restore backup-plans create "standard-backup-plan" \
    --location="us-central1" \
    --cluster="projects/${PROJECT_ID}/locations/us-central1/clusters/source-cluster" \
    --selected-namespaces="default" \
    --include-secrets \
    --include-volume-data
  ```

1. Make a backup

  ```bash
  gcloud beta container backup-restore backups create "standard-backup" \
    --location="us-central1" \
    --backup-plan="standard-backup-plan" \
    --wait-for-completion
  ```

1. Prepare to restore app by deleting ingress

  ```bash
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" delete ingress frontend
  ```

1. Create restore plan

  ```bash
  gcloud beta container backup-restore restore-plans create "autopilot-restore-plan" \
    --location="us-east1" \
    --backup-plan="projects/${PROJECT_ID}/locations/us-central1/backupPlans/standard-backup-plan" \
    --cluster="projects/${PROJECT_ID}/locations/us-east1/clusters/destination-cluster" \
    --namespaced-resource-restore-mode="delete-and-restore" \
    --selected-namespaces="default" \
    --transformation-rules-file="extras/backup/transformation-rules.yaml" \
    --volume-data-restore-policy="restore-volume-data-from-backup"
  ```

1. Restore BoA app to Destination cluster

  ```bash
  gcloud beta container backup-restore restores create "autopilot-restore" \
    --location="us-east1" \
    --restore-plan="autopilot-restore-plan" \
    --backup="projects/${PROJECT_ID}/locations/us-central1/backupPlans/standard-backup-plan/backups/standard-backup" \
    --wait-for-completion
  ```

1. Wait while BoA spinup in Destination cluster and check that populated data still there

1. Clean up

  ```bash
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" delete -f extras/backup/kubernetes-manifests/
  kubectl --context="gke_${PROJECT_ID}_us-central1_source-cluster" delete -f kubernetes-manifests/
  kubectl --context="gke_${PROJECT_ID}_us-east1_destination-cluster" delete -f extras/backup/kubernetes-manifests/
  kubectl --context="gke_${PROJECT_ID}_us-east1_destination-cluster" delete -f kubernetes-manifests/

  gcloud beta container backup-restore restores delete "autopilot-restore" \
    --location="us-east1" \
    --restore-plan="autopilot-restore-plan" \
    --quiet
  gcloud beta container backup-restore restore-plans delete "autopilot-restore-plan" \
    --location="us-east1" \
    --quiet
  gcloud beta container backup-restore backups delete "standard-backup" \
    --location="us-central1" \
    --backup-plan="standard-backup-plan" \
    --quiet
  gcloud beta container backup-restore backup-plans delete "standard-backup-plan" \
    --location="us-central1" \
    --quiet
  gcloud container clusters delete "source-cluster" --zone="us-central1" --quiet
  gcloud container clusters delete "destination-cluster" --region="us-east1" --quiet
  ```
