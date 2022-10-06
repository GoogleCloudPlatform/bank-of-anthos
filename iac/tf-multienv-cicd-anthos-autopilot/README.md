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

## Step-by-step with shell script support
1. Clone the Github Repository with your user.
1. Create a GCP project and note the `PROJECT_ID`.
1. Set up repository connection in Cloud Build
    1. Open Cloud Build in Cloud Console (enable API if needed).
    1. Navigate to 'Triggers' and set Region to `global`.
    1. Click `Manage Repositories`
    1. `CONNECT REPOSITORY` and follow the UI. Do NOT create a trigger.
1. [OPTIONAL] If your GCP organization has the compute.vmExternalIpAccess constraint in place reset it on project level `gcloud org-policies reset constraints/compute.vmExternalIpAccess --project=$PROJECT_ID` 
1. Replace environment variables in $REPO_ROOT/iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/env.sh
1. Navigate to the repository root and execute with project owner permissions `./iac/tf-multienv-cicd-anthos-autopilot/shell-scripts/00-setup-all-the-things.sh`. What happens under the hood:
    1. Patches ACM manifests to contain references to your project and commits them to your git repository
    1. Terraform will set up your GCP infrastructure
    1. Waits for provisioning of managed ASM to complete
    1. Deploys jobs to staging and production k8s clusters which initialise the Cloud SQL databases.
    1. Triggers CICD for accounts, frontend & ledger teams
1. Wait...
1. Enjoy!

# Troubleshooting
1. Sometimes the one-click-setup fails (e.g. because autopilot clusters need to be repaired, ASM is re-provisioning data plane, shell timeout). In that case just run the 00-setup-all-the-things.sh again as it is idempotent.

