# Set up project

Create project and note $PROJECT_ID (may contain a number in addition to project name!)
```
export PROJECT_ID=<PROJECT_ID>
```

# Set project for gcloud
```
gcloud config set project $PROJECT_ID
```

# Disable org-policies restricting autopilot usage if necessary:
```
gcloud org-policies reset constraints/compute.vmExternalIpAccess --project=$PROJECT_ID
```

# Set up terraform

https://learn.hashicorp.com/tutorials/terraform/install-cli (not necessary in cloud console)
```
gcloud auth application-default login
```
	
# Set desired values in terraform.tfvars
Example
```
project_id="bank-of-anthos-tf"
region="europe-west1"
zone="europe-west1-b"
registry_name="bank-of-anthos"
```


# Run pulumi
```	
terraform apply
```

Wait.... Profit!

# Run below commands. 
This will:

- Get credentials for the development cluster
- get artifactsregistry credentials 
- set the default repo for skaffold so you can simply do `skaffold dev`
- Annotate default service account in development so workloads can write metrics and traces
- Push to newly created repo which triggers Cloud Build and directly deploys to `staging` can then be manually promoted to `production`

```
gcloud container clusters get-credentials staging --region europe-west1 --project=$PROJECT_ID && kubectl annotate serviceaccount default --namespace=default iam.gke.io/gcp-service-account=gke-workload@$PROJECT_ID.iam.gserviceaccount.com && \

gcloud container clusters get-credentials production --region europe-west1 --project=$PROJECT_ID && kubectl annotate serviceaccount default --namespace=default iam.gke.io/gcp-service-account=gke-workload@$PROJECT_ID.iam.gserviceaccount.com && \

gcloud container clusters get-credentials development --region europe-west1 --project=$PROJECT_ID && kubectl annotate serviceaccount default --namespace=default iam.gke.io/gcp-service-account=gke-workload@$PROJECT_ID.iam.gserviceaccount.com && \

gcloud auth configure-docker europe-west1-docker.pkg.dev && \

skaffold config set default-repo europe-west1-docker.pkg.dev/$PROJECT_ID/bank-of-anthos && \

git remote add $PROJECT_ID https://source.developers.google.com/p/$PROJECT_ID/r/bank-of-anthos && \

git push --all $PROJECT_ID
```