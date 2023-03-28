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
    1. Navigate to 'Triggers' and set Region to the region that you want to use for the Bank of Anthos deployment.
    1. Click `Manage Repositories`
    1. `CONNECT REPOSITORY` and follow the UI. Do NOT create a trigger.
1. [OPTIONAL] If your GCP organization has the compute.vmExternalIpAccess constraint in place reset it on project level `gcloud org-policies reset constraints/compute.vmExternalIpAccess --project=$PROJECT_ID` 

## Replace placeholder variables in Anthos Config Management configuration [ONLY NECESSARY FOR PROJECTS OTHER THAN bank-of-anthos-ci]
1. Export `PROJECT_ID` and `REGION` as variables.
   ```bash
   export PROJECT_ID="YOUR_PROJECT_ID"
   export REGION="YOUR_REGION"
   ```
1. Replace all occurrences of `bank-of-anthos-ci` in `iac/acm-multienv-cicd-anthos-autopilot` with your chosen `PROJECT_ID`.
   ```bash
   # run from repository root
   find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/bank-of-anthos-ci/'"$PROJECT_ID"'/g' {} +
   ```
1. Replace all occurrences of `us-central1` in `iac/acm-multienv-cicd-anthos-autopilot` with your chosen `REGION`.
   ```bash
   # run from repository root
   find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/us-central1/'"$REGION"'/g' {} +
   ```
1. Commit and push your changes to your repository.
   ```bash
   git add .
   git commit -m "substitute $PROJECT_ID and $REGION references in ACM config"
   git push
   ```

## Replace domain in for production deployment
1. Export `DOMAIN` as variable.
   ```bash
   export DOMAIN="YOUR_DOMAIN"
   ```
1. Replace all occurrences of `bank-of-anthos` in `iac/acm-multienv-cicd-anthos-autopilot` with your chosen `DOMAIN`.
   ```bash
   # run from repository root
   find src/frontend/* -type f -exec sed -i 's/bank-of-anthos.xyz/'"$DOMAIN"'/g' {} +
   ```
1. Commit and push your changes to your repository.
   ```bash
   git add .
   git commit -m "substitute $PROJECT_ID and $REGION references in ACM config"
   git push
   ```

## Provision infrastructure with terraform
1. Create a GCS bucket in your project to hold your terraform state. `gsutil mb gs://$YOUR_TF_STATE_GCS_BUCKET_NAME`
1. Replace "YOUR_TF_STATE_GCS_BUCKET_NAME" in `iac/tf-multienv-cicd-anthos-autopilot/main.tf` with your chosen bucket name.
1. Configure terraform variables in `iac/tf-multienv-cicd-anthos-autopilot/terraform.tfvars` - at a minimum set `project_id` and `region` to the same values you used for the ACM substitution.
1. Provision infrastructure with terraform.
   ```bash
   # run from iac/tf-multienv-cicd-anthos-autopilot
   terraform init
   terraform apply
   ```
1. Check terraform output and approve terraform apply.
1. **Wait for ASM to be provisioned on all clusters!** Check the status with `gcloud container fleet mesh describe` and wait for all entries to be in `state: ACTIVE`. This will take dozens of minutes initially.
1. **Wait for Anthos Config Management to have synced the clusters (otherwise namespaces, service accounts will not be available)!** Check the status [here](https://console.cloud.google.com/anthos/config_management/dashboard). This will take dozens of minutes initially.

## Initialize CloudSQL databases with data (dummy users, transactions...)
1. Initialize `staging` CloudSQL database with data.
   ```bash
   echo '🔑  Getting cluster credentials...'
   gcloud container fleet memberships get-credentials staging-membership
   
   echo '🙌  Deploying populate-db jobs for staging...'
   skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
   skaffold run --profile=init-db-staging --module=accounts-db
   skaffold run --profile=init-db-staging --module=ledger-db
   
   echo '🕰  Wait for staging-db initialization to complete...'
   kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-staging --timeout=300s
   ```
1. Initialize `production` CloudSQL database with data.
   ```bash
   echo '🔑  Getting cluster credentials...'
   gcloud container fleet memberships get-credentials production-membership
   
   echo '🙌  Deploying populate-db jobs for production...'
   skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
   skaffold run --profile=init-db-production --module=accounts-db
   skaffold run --profile=init-db-production --module=ledger-db

   echo '🕰  Wait for production-db initialization to complete...'
   kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-staging --timeout=300s
   ```

## Run the first deployment of the application manually as otherwise E2E tests will fail it
1. Staging
```bash
   gcloud container fleet memberships get-credentials staging-membership
   skaffold run -p staging --skip-tests=true
```
2. Production
```bash
   gcloud container fleet memberships get-credentials production-membership
   skaffold run -p production --skip-tests=true
```

## Deploy the application through CI/CD
1. Execute CI/CD pipeline through Cloud Build triggers.
   ```bash
   echo '🌈  Triggering CI/CD for Frontend team'
   gcloud beta builds triggers run frontend-ci --branch $SYNC_BRANCH --region $REGION

   echo '😁  Triggering CI/CD for Accounts team'
   gcloud beta builds triggers run accounts-contacts-ci --branch $SYNC_BRANCH --region $REGION
   gcloud beta builds triggers run accounts-userservice-ci --branch $SYNC_BRANCH --region $REGION

   echo '📒  Triggering CI/CD for Ledger team'
   gcloud beta builds triggers run ledger-balancereader-ci --branch $SYNC_BRANCH --region $REGION
   gcloud beta builds triggers run ledger-ledgerwriter-ci --branch $SYNC_BRANCH --region $REGION
   gcloud beta builds triggers run ledger-transactionhistory-ci --branch $SYNC_BRANCH --region $REGION
   ```

# Troubleshooting
1. Sometimes `terraform apply` fails due to a timeout or race conditions from API-enablement. In that case simply run `terraform apply` again.
2. Sometimes the database seeding jobs' pods get stuck due to a failed sidecar container. This can be easily fixed by deleting the pods stuck with 2/3 containers.
3. For production deployment ensure that DNS for your `$DOMAIN` has been set up to point to the IP of the production ingress. 
```
kubectl get ingress frontend-ingress --namespace bank-of-anthos-production -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```
