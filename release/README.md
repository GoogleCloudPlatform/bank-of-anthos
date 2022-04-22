# Releasing Bank of Anthos

This document describes how maintainers can tag and push a new release of Bank of Anthos.

## Prerequisites for tagging a release

1. **Manually test** the latest main commit by verifying the user journeys below. If you encounter any bugs or documentation in need of fixing, make those changes before proceeding with the release.

- User can deploy Bank of Anthos on a new GCP project/GKE cluster following README instructions, replacing `kubernetes-manifests/` with `dev-kubernetes-manifests/`
- User can deploy Bank of Anthos on a GKE cluster with the latest Anthos Service Mesh enabled, by deploying `istio-manifests/` on top of the kubernetes manifests
- User can deploy Bank of Anthos on a GKE cluster with Workload Identity enabled, using the WI instructions in the README.
- User can see Java app-level metrics by creating the Cloud Monitoring dashboard in the `extras/` directory
- User can see traces in Cloud Trace
- User can toggle `ENABLE_METRICS=false` and `ENABLE_TRACING=false` to turn off metrics and trace export to Cloud Operations
- User can create an account and see expected home page
- User is blocked from signing in with bad credentials
- User can create account and see zero balance
- User can deposit funds, see balance update, see transaction history, see new contact show up
- can transfer funds, see balance update, see transaction in history, see new contact show up
- User is blocked from sending invalid data
- User is redirected from `/home` to `/login` when not authenticated
- User is redirected from `/login` and `/signup` to `/home` when already authenticated
- Makefile commands work as intended
- Makefile commands reflect what is in docs

2. **Choose the logical [next release tag](https://github.com/GoogleCloudPlatform/bank-of-anthos/releases)**, using [semantic versioning](https://semver.org/): `vX.Y.Z`. If this release includes significant feature changes, update the minor version (`Y`). Otherwise, for bug-fix releases or standard quarterly release, update the patch version `Z`).

## Tag the new release

Make sure that the following commands are in your `PATH`:
- `realpath` (found in the `coreutils` package)
- `skaffold`
- `gcloud`

Run the `make-release.sh` script found inside the `release` directory:

```sh
# assuming you are inside the root path of the bank-of-anthos repository
export NEW_VERSION=vX.Y.Z
export REPO_PREFIX=gcr.io/bank-of-anthos-ci
./release/make-release.sh
```

This script does the following:
1. Replaces the existing `kubernetes-manifests` with the content of `dev-kubernetes-manifests`.
2. Updates the image tags for all the Deployments in `kubernetes-manifests` with the new release tag.
3. Uses `git tag` to create a new local tag.
4. Creates a new release branch.
5. Uses `skaffold` to build and push new stable release images to `gcr.io/bank-of-anthos-ci`.
6. Pushes the git tag and the release branch.

### Troubleshooting script failures

In the event of any of the steps above failing you might have to revert the repository to its original state. Follow the steps below as required:
```sh
# delete the newly created release branch & tag before re-running the script
git checkout main
git branch -D release/$NEW_VERSION
git tag -d $NEW_VERSION

# delete temporary files created
rm kubernetes-manifests/*-e
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

First, make sure you are connected to the production cluster (**note:** this requires authorization access to the Bank of Anthos cluster):
```
gcloud container clusters get-credentials bank-of-anthos-release --zone us-central1-c --project bank-of-anthos-ci
```

1. ***[Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) enabled production cluster***

Currently the `bank-of-anthos-release` cluster has [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) enabled. Thus, when deploying to this cluster the pod service account (`boa-ksa-release`) used by _Workload Identity_ must be used as the serviceAccount in the manifests.

Follow steps 3 and 4 of the [workload identity setup](https://github.com/GoogleCloudPlatform/bank-of-anthos/blob/main/docs/workload-identity.md) with the following config values to deploy into production:
- `boa-ksa-release` as the `KSA_NAME`
- `default` as the `NAMESPACE`

2. ***Non Workload Identity cluster***

You can simply apply the new manifest versions on top of the current environment:
```
kubectl apply -f ./kubernetes-manifests
```

Alternatively, you can also choose to start from scratch by deleting the previously applied manifests first:
```
kubectl delete -f kubernetes-manifests
kubectl apply -f ./kubernetes-manifests
```

## Announce the new release internally

Once the new release is out, you can now announce it via [g/bank-of-anthos-announce](https://groups.google.com/a/google.com/g/bank-of-anthos-announce).
