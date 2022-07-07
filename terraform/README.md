# Anthos Sample Deployment (ASD) proof of concept (POC)

Deploy ASD via Terraform and ACM

#TODO: ## Add detailed instructions for deploying the sample

1. Clone the repo `git clone https://github.com/GoogleCloudPlatform/bank-of-anthos.git` 
1. `export TF_VAR_project=<your project id>` Set $TF_VAR_project enviornment variable to a project that has billing enabled
1. `gcloud auth application-default login` to enable Terraform to use the default service account
1. `cd terraform`
1. `terraform init`
1. `terraform plan`
1. `terraform apply`