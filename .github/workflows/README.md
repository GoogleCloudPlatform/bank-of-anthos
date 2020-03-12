# GitHub Actions Workflows

workloads run using [GitHub self-hosted runners](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/about-self-hosted-runners)

Ensure `MASTER_CLUSTER` `PROJECT_ID` and `ZONE` are set in the [repo's secrets](https://github.com/GoogleCloudPlatform/anthos-finance-demo/settings/secrets)

## Setup

1. Create a GCE instance for running tests
    - VM should be at least n1-standard-4 with 50GB persistent disk
    - VM should use custom service account with only permissions to push images to GCR
2. SSH into new VM through Google Cloud Console
3. Follow the instructions to add a new runner on the [Actions Settings page](https://github.com/GoogleCloudPlatform/anthos-finance-demo/settings/actions) to authenticate the new runner
4. Set GitHub Actions as a background service
    - `sudo ~/actions-runner/svc.sh install ; sudo ~/actions-runner/svc.sh start`
5. Run the following command to install dependencies
    - `wget -O - https://github.com/GoogleCloudPlatform/anthos-finance-demo/blob/master/.github/workflows/install-dependencies.sh | bash`

---
## Workflows

### Smoketests.yaml

#### Triggers
- commits pushed to master
- PRs to master
- PRs to release/ branches

#### Actions
- runs java and python linters
- ensures kind cluster is running
- builds all containers in src/
- deploys local containers to kind
  - ensures all pods reach ready state
  - ensures HTTP request to frontend returns HTTP status 200
- deploys manifests from /releases
  - ensures all pods reach ready state
  - ensures HTTP request to frontend returns HTTP status 200

### Push-Deploy.yml

#### Triggers
- commits pushed to master

#### Actions
- builds and pushes containers to gcr.io/bank-of-anthos
  - tagged with git commit hash and `latest`
