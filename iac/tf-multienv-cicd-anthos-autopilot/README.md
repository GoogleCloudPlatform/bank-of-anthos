# Disclaimer
This configuration is **not meant for everyday usage** and is **not required to deploy Bank of Anthos or any of its extensions / flavours**. Instead it is meant to showcase a full-featured CI/CD environment based on Cloud Build, Cloud Deploy, skaffold & kustomize that deploys to multiple GKE Autopilot-based runtime environments with valuable Anthos features like Anthos Service Mesh and Anthos Config Management enabled.

# What does this solution contain?
- CI per team (accounts, frontend, ledger) with skaffold profile per environment
- CD per team (accounts, frontend, ledger) with skaffold profile per environment
- Development environment:
    - GKE Autopilot /w managed ASM (namespace: bank-of-anthos-development)
    - ACM for base setup
    - In-cluster databases
- Staging environment:
    - GKE Autopilot /w managed ASM (namespace: bank-of-anthos-staging)
    - ACM for base setup
    - Cloud SQL database
    - deployed from Cloud Deploy
- Production environment:
    - GKE Autopilot /w managed ASM (namespace: bank-of-anthos-production)
    - ACM for base setup
    - Cloud SQL database
    - deployed from Cloud Deploy
- heavy use of kustomize components & skaffold profiles to keep it DRY
- minimal service account permissions
- Cloud Foundation Toolkit for GKE

# How to set it up


## Prerequisites

Setting up the sample requires that you have a [Google Cloud Platform (GCP) project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#console), connected to your billing account.

## Github repository setup
1. Clone the Github Repository with your user.
1. Create a GCP project and note the `PROJECT_ID`.
1. Set up repository connection in Cloud Build
    1. Open Cloud Build in Cloud Console (enable API if needed).
    1. Navigate to 'Triggers' and set Region to `global`.
    1. Click `Manage Repositories`
    1. `CONNECT REPOSITORY` and follow the UI. Do NOT create a trigger.
1. [OPTIONAL] If your GCP organization has the compute.vmExternalIpAccess constraint in place reset it on project level `gcloud org-policies reset constraints/compute.vmExternalIpAccess --project=$PROJECT_ID` 

## Replace placeholder variables in Anthos Config Management configuration
1. Export `PROJECT_ID` and `REGION` as variables.
   ```bash
   export PROJECT_ID="YOUR_PROJECT_ID"
   export REGION="YOUR_REGION"
   ```
1. Replace all occurrences of `$PROJECT_ID` in `iac/acm-multienv-cicd-anthos-autopilot` with your noted `PROJECT_ID`.
   ```bash
   # run from repository root
   find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/$PROJECT_ID/'"$PROJECT_ID"'/g' {} +
   ```
1. Replace all occurrences of `$REGION` in `iac/acm-multienv-cicd-anthos-autopilot` with your chosen `REGION`.
   ```bash
   # run from repository root
   find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/$REGION/'"$REGION"'/g' {} +
   ```
1. Commit and push your changes to your repository.
   ```bash
   git commit -m "substitute $PROJECT_ID and $REGION references in ACM config"
   git push
   ```

## Provision infrastructure with terraform
1. Create a GCS bucket in your project to hold your terraform state. `gsutil mb gs://$YOUR_TF_STATE_GCS_BUCKET_NAME`
1. Replace "YOUR_TF_STATE_GCS_BUCKET_NAME" in `iac/tf-multienv-cicd-anthos-autopilot/main.tf` with your chosen bucket name.
1. Configure terraform variables in `iac/tf-multienv-cicd-anthos-autopilot/terraform.tfvars` - at a minimum replace `$PROJECT_ID` and `$REGION` with the same values you used for the ACM substitution.
1. Provision infrastructure with terraform.
   ```bash
   # run from iac/tf-multienv-cicd-anthos-autopilot
   terraform init
   terraform apply
   ```
1. Check terraform output and approve terraform apply.
1. Wait for ASM to be provisioned on all clusters. Check the status with `gcloud container fleet mesh describe` and wait for all entries to be in `state: ACTIVE`. This might take between dozens of minutes.

## Initialize CloudSQL databases with data (not ready in this PR due to dependencies on skaffold/kustomize configuration)
1. Initialize `staging` CloudSQL database with data.
   ```bash
   echo '🔑  Getting cluster credentials...'
   gcloud container fleet memberships get-credentials staging-membership
   
   echo '🙌  Deploying populate-db jobs for staging...'
   skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
   skaffold run --profile=init-db-staging
   
   echo '🕰  Wait for staging-db initialization to complete...'
   kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-staging --timeout=300s
   ```
1. Initialize `production` CloudSQL database with data.
   ```bash
   echo '🔑  Getting cluster credentials...'
   gcloud container fleet memberships get-credentials production-membership
   
   echo '🙌  Deploying populate-db jobs for staging...'
   skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
   skaffold run --profile=init-db-production

   echo '🕰  Wait for staging-db initialization to complete...'
   kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-staging --timeout=300s
   ```

## Deploy the application (not ready in this PR due to dependencies on skaffold/kustomize configuration)
1. Execute CI/CD pipeline through Cloud Build triggers.
   ```bash
   echo '🌈  Triggering CI/CD for Frontend team'
   gcloud beta builds triggers run frontend-ci --branch $SYNC_BRANCH

   echo '😁  Triggering CI/CD for Accounts team'
   gcloud beta builds triggers run accounts-ci --branch $SYNC_BRANCH

   echo '📒  Triggering CI/CD for Ledger team'
   gcloud beta builds triggers run ledger-ci --branch $SYNC_BRANCH
   ```

# Troubleshooting
1. Sometimes `terraform apply` fails due to a timeout or race conditions from API-enablement. In that case simply run `terraform apply` again.
