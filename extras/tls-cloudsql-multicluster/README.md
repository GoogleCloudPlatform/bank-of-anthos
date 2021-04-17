# Cloud SQL Multicluster with a TLS Frontend 

This directory deploys the [Cloud SQL + Multicluster](/extras/cloudsql-multicluster/README.md) flavor of Bank of Anthos, but configures the Multi-cluster Ingress resource to use TLS with self-signed certificates, and enforces an HTTP->HTTPS redirect for all inbound traffic. 


## Prerequisites

- Install the kubectx command line tool
- Anthos license

## Steps

1. **Create a [Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)** if you don't already have one.

2. **Set environment variables**, where `DB_REGION` is where the Cloud SQL instance will be deployed


```
export PROJECT_ID="my-project"
export DB_REGION="us-central1"
export CLUSTER_1_NAME="boa-1"
export CLUSTER_1_ZONE="us-central1-b"
export CLUSTER_2_NAME="boa-2"
export CLUSTER_2_ZONE="europe-west3-a"
export NAMESPACE="default"
```

3. Run the setup script. This will create 2 GKE clusters, register them to the Anthos dashboard, then create a Cloud SQL instance. 

```
./setup.sh
```


4. Get the MCI status. 

```
watch kubectl describe mci frontend-global-ingress -n ${NAMESPACE}
```