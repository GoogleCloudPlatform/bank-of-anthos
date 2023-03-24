# GKE Autopilot

Terraform configuration for GKE Autopilot cluster.

To apply configuration:

```shell
terraform init
terraform apply
```

## Access the cluster

```shell
gcloud container clusters get-credentials --region=$(terraform output -raw region) $(terraform output -raw cluster_name)
```
