# Development Guide

To develop the Bank of Anthos application locally, you will need:

- a GCP project
- the `PROJECT_ID` variable set to your project
- one GKE cluster (with at least 4 nodes, recommended machine type `n1-standard-4`)
- [skaffold]() and [kubectl]() installed to your local environment


### Build images and deploy once

```
skaffold run --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos
```

### Build images and deploy continuously

Use `skaffold dev` to automatically propagate code changes to your cluster on file save.

```
skaffold dev --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos
```


## Continuous Integration

GitHub Actions workflows [described here](./.github/workflows)