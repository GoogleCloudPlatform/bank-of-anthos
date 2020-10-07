# Running in Kubernetes Environments


## GKE on GCP 

Use the default instructions in the [README](/README.md). When Workload Identity is enabled, use the [Workload Identity instructions](/docs/workload-identity.md).  

## AWS EKS 

Use the default README instructions, but note that currently, metrics and trace export to Google Cloud Operations does not currently work. In the Deployment manifests, set `ENABLE_METRICS=false` and `ENABLE_TRACING=false` to prevent any pod crashes on startup.
