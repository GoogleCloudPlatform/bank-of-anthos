# Releasing Bank of Anthos

This document describes how maintainers can tag and push a new release of Bank of Anthos.

## Prerequisites for tagging a release

1. Manually test the latest main commit by verifying the user journeys below:

   - User can deploy Bank of Anthos on a new GCP project/GKE cluster following README instructions.
   - User can deploy Bank of Anthos on a GKE cluster with the latest Anthos Service Mesh enabled, by deploying `extras/istio-manifests/` on top of the kubernetes manifests.
   - User can see Java app-level metrics by creating the Cloud Monitoring dashboard in the `extras/metrics-dashboard/` directory.
   - User can see traces in Cloud Trace.
   - User can toggle `ENABLE_METRICS=false` and `ENABLE_TRACING=false` to turn off metrics and trace export to Cloud Operations.
   - User can create an account and see expected home page.
   - User is blocked from signing in with bad credentials.
   - User can create account and see zero balance.
   - User can deposit funds, see balance update, see transaction history, see new contact show up.
   - User can transfer funds, see balance update, see transaction in history, see new contact show up.
   - User is blocked from sending invalid data.
   - User is redirected from `/home` to `/login` when not authenticated.
   - User is redirected from `/login` and `/signup` to `/home` when already authenticated.

2. Choose the logical [next release tag](https://github.com/GoogleCloudPlatform/bank-of-anthos/releases), using [semantic versioning](https://semver.org/): `vX.Y.Z`.

   If this release includes significant feature changes, update the minor version (`Y`). Otherwise, for bug-fix releases or standard quarterly release, update the patch version `Z`).

3. Ensure that the following commands are in your `PATH`:
   - `realpath` (found in the `coreutils` package)
   - `skaffold`
   - `gcloud`

4. Make sure that your `gcloud` is authenticated:

   ```sh
   gcloud auth login
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

## Create and tag the new release

Run the `make-release.sh` script found inside the `docs/releasing` directory:

```sh
# assuming you are inside the root path of the bank-of-anthos repository
export NEW_VERSION=vX.Y.Z
export REPO_PREFIX=us-central1-docker.pkg.dev/bank-of-anthos-ci/bank-of-anthos
./docs/releasing/make-release.sh
```

This script does the following:
1. Clears out the previous release in `kubernetes-manifests/`.
2. Build, tag, and pushes release images in Artifact Registry using `skaffold build`.
3. Renders new k8s manifests using `skaffold render`.
4. Update version environment variables in k8s and TF manifests.
5. Creates a new git release branch and tag.
6. Pushes the git release branch and tag upstream.

### Troubleshooting script failures

In the event of any of the steps above failing you might have to revert the repository to its original state. Follow the steps below as required:
```sh
# delete the newly created release branch & tag before re-running the script
git checkout main
git branch -D release/$NEW_VERSION
git tag -d $NEW_VERSION
```

## Create the PR

Now that the release branch has been created, you can find it in the [list of branches](https://github.com/GoogleCloudPlatform/bank-of-anthos/branches) and create a pull request targeting `main` (the default branch).

This process is going to trigger multiple CI checks as well as stage the release onto a temporary cluster. Once the PR has been approved and all checks are successfully passing, you can now merge the branch.

## Add notes to the release

Once the PR has been fully merged, you are ready to create a new release for the newly created [tag](https://github.com/GoogleCloudPlatform/bank-of-anthos/tags).
- Click the breadcrumbs on the row of the latest tag that was created in the [tags](https://github.com/GoogleCloudPlatform/bank-of-anthos/tags) page
- Select the `Create release` option

The release notes should contain a brief description of the changes since the previous release (like bug fixed and new features). For inspiration, you can look at the list of [releases](https://github.com/GoogleCloudPlatform/bank-of-anthos/releases).

> ***Note:*** No assets need to be uploaded. They are picked up automatically from the tagged revision

## Deploy on the production environment

Once the release notes are published, you should then replace the version of the production environment to the newly published version.

1. Open up the [Cloud Deploy dashboard](https://pantheon.corp.google.com/deploy/delivery-pipelines?project=bank-of-anthos-ci).

2. For each service, click on it, verify that its staging version is green, and then click **Promote**.

   ![Cloud Deploy](/docs/img/cloud-deploy.png)

3. Wait for all promotion builds to be green.

4. Verify that the production environment is still up and running: https://cymbal-bank.fsi.cymbal.dev

## Update the ledgermonolith bucket

If changes has been made to the ledgermonolith, the artifacts need to be built and pushed to the GCS bucket:
```
export PROJECT_ID=bank-of-anthos-ci
export GCS_BUCKET=bank-of-anthos-ci
export ZONE=us-central1-c
make monolith-build
```

## Announce the new release internally

Once the new release is out, you can now announce it via [g/bank-of-anthos-announce](https://groups.google.com/a/google.com/g/bank-of-anthos-announce).
