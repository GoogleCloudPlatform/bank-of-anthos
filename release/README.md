# Bank of Anthos Release Workflow

This doc describes how repo maintainers can tag and push a new release. 


## Prerequisites for tagging a release 

1. **Complete a team-wide Fishfood day** off the latest master commit. Divide and conquer tasks, to test and verify the user journeys below. If you encounter any bugs or docs in need of fixing, make those changes before proceeding with the release. 

- User can deploy Bank of Anthos on a new GCP project/GKE cluster following README instructions, replacing `kubernetes-manifests/` with `dev-kubernetes-manifests/` 
- User can deploy Bank of ANthos on a GKE cluster with the latest Anthos Service Mesh enabled, by deploying `istio-manifests/` on top of the kubernetes manifests 
- User can deploy Bank of Anthos on a GKE cluster with Workload Identity enabled, using the WI instructions in the README.
- User can see Java app-level metrics by creating the Cloud Monitoring dashboard in the `extras/` directory 
- User can see traces in Cloud Trace
- User can toggle `ENABLE_METRICS=false` and `ENABLE_TRACING=false` to turn off metrics/trace export to Cloud Operations
- User can create an account and see expected home page
- User is blocked from signing in with bad credentials
- User can create account and see zero balance
- User can deposit funds, see balance update, see transaction history, see new contact show up
- can transfer funds, see balance update, see transaction in history, see new contact show up
- User is blocked from sending invalid data
- User is redirected from /home to /login when not authenticated
- User is redirected from /login and /signup to /home when already authenticated
- Makefile commands work as intended
- Makefile commands reflect what is in docs


2. **Choose the logical [next release tag](https://github.com/GoogleCloudPlatform/bank-of-anthos/releases)**, using [semantic versioning](https://semver.org/): `vX.Y.Z`. If this release includes significant feature changes, update the minor version (`Y`). Otherwise, for bug-fix releases or standard quarterly release, update the patch version `Z`). 


## Tagging a release 

When you're ready, run the `make-release.sh` script. 

```
export NEW_VERSION=vX.Y.Z
export REPO_PREFIX=gcr.io/bank-of-anthos
./make-release.sh
```


This script does the following: 

1. Replaces the existing `kubernetes-manifests` with the contents of `dev-kubernetes-manifests`. 
2. Updates the image tag for all the Deployments in the new `kubernetes-manifests`, with the new release tag. 
3. Uses `git tag` to create a new local release 
4. Creates a new release branch 
5. Uses `skaffold` to build and push new stable release images to `gcr.io/bank-of-anthos` 
6. Pushes the Git tags, and the release branch. 

