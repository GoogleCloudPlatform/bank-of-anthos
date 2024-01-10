# CI/CD pipeline

This document introduces the CI/CD pipeline that powers Bank of Anthos' production instance (hosted here: https://cymbal-bank.fsi.cymbal.dev/) as well as how you can get started deploying it in your own Google Cloud project (with your own domain name).

**Note**: This is a more advanced view of Bank of Anthos and is _not_ required to deploy Bank of Anthos or any of its deployment options. Instead, this is meant to showcase how one can deploy a full end-to-end CI/CD environment with [Cloud Build](https://cloud.google.com/build) and [Cloud Deploy](https://cloud.google.com/deploy), with the help of [Terraform](https://www.terraform.io/), [Skaffold](https://skaffold.dev/), and [Kustomize](https://kustomize.io/). The end result is multiple environments in a multi-stage pipeline (development, staging, production) which features [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine), [Anthos Config Management (ACM)](https://cloud.google.com/anthos/config-management), [Anthos Service Mesh (ASM)](https://cloud.google.com/anthos/service-mesh), and [Cloud SQL](https://cloud.google.com/sql/docs).

## What does this solution contain?

The CI/CD pipeline set-up includes:

- Terraform scripts for all Google Cloud resources
- 3 GKE Autopilot clusters in a fleet
- 1 Cloud Build trigger for GitHub PRs
- 6 Cloud Build triggers for staging (1 per service)
- 2 Cloud SQL databases (1 for staging, 1 for production)
- 2-stage Cloud Deploy pipelines (staging and production)
- Anthos Config Management set-up for staging and production
- Anthos Service Mesh set-up for staging and production
- Artifact Registry repository for container images
- Cloud Storage bucket for Terraform state
- Cloud Storage bucket for ledger monolith artifacts
- IAM bindings and service accounts

This results in:

- CI per service with Skaffold profile per environment
- CD per service with Skaffold profile per environment
- Development environment:
  - GKE Autopilot (one namespace per deployment)
  - ACM for base setup
  - In-cluster databases
  - Deployed from Cloud Build
- Staging environment:
  - GKE Autopilot
  - Anthos Config Management for base setup
  - Anthos Service Mesh (namespace: `bank-of-anthos-staging`)
  - Cloud SQL database
  - Deployed from Cloud Deploy
- Production environment:
  - GKE Autopilot
  - ACM for base setup
  - Anthos Service Mesh (namespace: `bank-of-anthos-production`)
  - Cloud SQL database
  - Deployed from Cloud Deploy
- Use of kustomize components & skaffold profiles to keep it DRY
- Minimal service account permissions
- Cloud Foundation Toolkit for GKE

## Set-up instructions

### Prerequisites

To deploy the CI/CD pipeline, you need:

- [Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#console), connected to an active billing account
- A domain name for the production deployment.
- The `gcloud`, `kubectl`, `skaffold`, `terraform` command line tools

1. Clone the GitHub repository.

   ```sh
   git clone https://github.com/GoogleCloudPlatform/bank-of-anthos
   ```

   **Note**: If you are deploying this pipeline in your own Google Cloud project, it is preferable to first fork the repository, to be able to commit variable changes.

1. Set environment variables.
   ```sh
   export PROJECT_ID="YOUR_PROJECT_ID"
   export REGION="YOUR_REGION"
   export DOMAIN="YOUR_DOMAIN"
   ```

### Setting-up GitHub repository connection

1. Set up a repository connection in Cloud Build:
   1. Open Cloud Build in Cloud Console (enable its API if needed).
   1. Navigate to _Triggers_ and set _Region_ to your preferred region.
   1. Click on _Manage repositories_.
   1. Click on _Connect repository_ and follow the UI. Do _not_ create a trigger.
1. [Optional] If your Google Cloud organization has the `compute.vmExternalIpAccess` constraint in place, you can reset it on a project level:
   ```sh
   gcloud org-policies reset constraints/compute.vmExternalIpAccess --project=$PROJECT_ID`
   ```

### Updating placeholder variables

These steps are necessary for all Google Cloud projects that are _not_ `bank-of-anthos-ci`. If you are deploying the CI/CD pipeline for the official Bank of Anthos deployment, _skip this section_.

1. Replace all occurrences of `bank-of-anthos-ci` in the Terraform scripts with your Google Cloud project ID.
   ```sh
   # run from repository root
   find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/bank-of-anthos-ci/'"$PROJECT_ID"'/g' {} +
   find iac/tf-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/bank-of-anthos-ci/'"$PROJECT_ID"'/g' {} +
   ```
1. Replace all occurrences of `us-central1` in the Terraform scripts with your preferred region.
   ```sh
   # run from repository root
   find iac/acm-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/us-central1/'"$REGION"'/g' {} +
   find iac/tf-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/us-central1/'"$REGION"'/g' {} +
   ```
1. Replace all occurrences of `bank-of-anthos-tf-state` in the Terraform scripts with your bucket.
   ```sh
   # run from repository root
   find iac/tf-multienv-cicd-anthos-autopilot/* -type f -exec sed -i 's/bank-of-anthos-tf-state/'"$PROJECT_ID-boa-tf-state"'/g' {} +
   ```
1. Replace all occurrences of `cymbal-bank.fsi.cymbal.dev` in the Terraform scripts with your domain name.
   ```sh
   # run from repository root
   find src/frontend/* -type f -exec sed -i 's/cymbal-bank.fsi.cymbal.dev/'"$DOMAIN"'/g' {} +
   ```
1. Commit and push your changes to your repository.
   ```sh
   git add .
   git commit -m "Substitute project ID, region, and domain references in ACM config"
   git push
   ```

### Provisioning the infrastructure

1. Create a Cloud Storage bucket in your project to hold your Terraform state.
   ```sh
   gsutil mb gs://${PROJECT_ID}-boa-tf-state
   gsutil versioning set on gs://${PROJECT_ID}-boa-tf-state
   ```
1. Verify the Terraform variables in `iac/tf-multienv-cicd-anthos-autopilot/terraform.tfvars`. In particular, `project_id` and `region` are set to the same values you used earlier.
1. Provision the infrastructure with Terraform.
   ```sh
   # run from iac/tf-multienv-cicd-anthos-autopilot
   terraform init && \
   terraform apply
   ```
1. Verify the Terraform output and approve it.
1. Wait for Anthos Service Mesh to be provisioned on all clusters. You can check the status with `gcloud container fleet mesh describe` and wait for all entries to be in `state: ACTIVE`. This may take several minutes to complete.
1. Wait for Anthos Config Management to have synced the clusters. You can check the status [here](https://console.cloud.google.com/anthos/config_management/dashboard). This may take several minutes.

### Initializing CloudSQL databases with sample data

1. Initialize the staging CloudSQL database with data.

   ```sh
   gcloud container fleet memberships get-credentials staging-membership

   skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
   skaffold run --profile=init-db-staging --module=accounts-db
   skaffold run --profile=init-db-staging --module=ledger-db

   kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-staging --timeout=300s
   ```

1. Initialize the production CloudSQL database with data.

   ```sh
   gcloud container fleet memberships get-credentials production-membership

   skaffold config set default-repo $REGION-docker.pkg.dev/$PROJECT_ID/bank-of-anthos
   skaffold run --profile=init-db-production --module=accounts-db
   skaffold run --profile=init-db-production --module=ledger-db

   kubectl wait --for=condition=complete job/populate-accounts-db job/populate-ledger-db -n bank-of-anthos-production --timeout=300s
   ```

### Deploying the application (manually)

Before we run the CI/CD pipelines, we should manually deploy the application once on the staging, and on the production clusters. This step is not necessary, but it will prevent end-to-end test failures when the CI triggers run for the first time.

1. Deploy Bank of Anthos on the staging environment.

   ```sh
   gcloud container fleet memberships get-credentials staging-membership
   skaffold run -p staging --skip-tests=true
   ```

2. Deploy Bank of Anthos on the production environment.

   ```sh
   gcloud container fleet memberships get-credentials production-membership
   skaffold run -p production --skip-tests=true
   ```

### Staging the application (through Cloud Build)

1. Run the Cloud Build CI triggers once for each service.
   ```sh
   gcloud beta builds triggers run frontend-ci --region $REGION
   gcloud beta builds triggers run accounts-contacts-ci --region $REGION
   gcloud beta builds triggers run accounts-userservice-ci --region $REGION
   gcloud beta builds triggers run ledger-balancereader-ci --region $REGION
   gcloud beta builds triggers run ledger-ledgerwriter-ci --region $REGION
   gcloud beta builds triggers run ledger-transactionhistory-ci --region $REGION
   ```

### Setting-up the DNS and certificate

1. In your domain registrar, add or modify an `A` route pointing to the production cluster.

   You can find the IP address in Cloud Load Balancing. Find the production ingress LB,
   and copy the IP that is listed. Alternatively:

   ```sh
   kubectl get ingress frontend-ingress --namespace bank-of-anthos-production -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
   ```

2. Wait for the certificate to be provisioned. This will show up in the Classic Certificates
   section of the Certificate Manager. Once provisioned, its state will change to _Active_.

3. Once the DNS and certificates are fully propagated, you should be able to access Bank of Anthos through `https://$DOMAIN`. Note that the propagation may take several minutes.

## Troubleshooting

- If `terraform apply` fails due to a timeout or race conditions from API-enablement, you can try simply running `terraform apply` again.
- Sometimes the database seeding jobs' pods get stuck due to a failed sidecar container. This can be easily fixed by deleting the pods stuck with 2/3 containers.
- For production deployment, ensure that the DNS for your `$DOMAIN` has been set up to point to the IP of the production ingress.
