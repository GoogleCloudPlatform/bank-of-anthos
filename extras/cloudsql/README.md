
# Cloud SQL + Bank of Anthos 

This directory contains instructions and Kubernetes manifests for overriding the default in-cluster PostgreSQL databases (`accountsdb` + `ledgerdb`) with Google Cloud SQL. 

![diagram](arch.png)

## How it works 

The setup scripts provided will provision a Cloud SQL instance in your Google Cloud Project. The script will then create two databases - one for the **accounts DB**, one for the **ledger DB**. This replaces the two separate PostgreSQL StatefulSets used in Bank of Anthos by default. 


## Setup 

1. Create a [Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) if you don't already have one. 

2. Customize the following environment variables for your project, desired GCP region/zone, and the Kubernetes namespace into which you want to deploy Bank of Anthos.

```
PROJECT_ID="my-project"
REGION="us-east1"
ZONE="us-east1-b" 
CLUSTER="my-cluster-name"
NAMESPACE="default"
```

3. Create a GKE cluster with [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#overview) enabled. Workload Identity lets you use a Kubernetes service account like a Google Cloud service account, giving your pods granular Google Cloud API permissions - in this case, permission for the Bank of Anthos Pods to access Cloud SQL. 

```
	gcloud container clusters create ${CLUSTER} \
		--project=${PROJECT_ID} --zone=${ZONE} \
		--machine-type=e2-standard-4 --num-nodes=4 \
    --workload-pool="${PROJECT_ID}.svc.id.goog"
```

4. Run the Workload Identity setup script for your new cluster. This script creates a Google Service Account (GSA) and Kubernetes Service Account (KSA), associates them together, then grants the service account permission to access Cloud SQL. 

```
./setup_workload_identity.sh
```

5. Run the Cloud SQL instance create script. This takes a few minutes to complete. 

```
./create_cloudsql_instance.sh 
```
6. Deploy the Bank of Anthos services to your cluster. Each backend deployment (`userservice`, `contacts`, `transactionhistory`, `balancereader`, and `ledgerwriter`) is configured with a [Cloud SQL Proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy#what_the_proxy_provides) sidecar container. Cloud SQL Proxy provides a secure TLS connection between the backend GKE pods and your Cloud SQL instance. 

This command will also deploy two Kubernetes Jobs, to populate the accounts and ledger dbs with Tables and test data. 


```
kubectl apply -n ${NAMESPACE} -f ./kubernetes-manifests 
```


7. Wait a few minutes for all the pods to be `RUNNING`. (Note that the two Jobs will run to completion.) 

```

```

Access the Bank of Anthos frontend at the following IP, then log in as `test-user` with the pre-populated credentials added to the Cloud SQL-based `accounts-db`. You should see the pre-populated transaction data show up, from the Cloud SQL-based `ledger-db`. You're done! 