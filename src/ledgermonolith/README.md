# Ledger Monolith Service

Reads and writes transactions belonging to the bank ledger.

Implemented in Java with Spring Boot and Guava.

### Endpoints

| Endpoint                    | Type | Auth? | Description                                                                 |
| --------------------------- | ---- | ----- | --------------------------------------------------------------------------- |
| `/balances/<accountid>`     | GET  | 🔒    | Get the account balance if owned by the currently authenticated user.       |
| `/healthy`                  | GET  |       | Liveness probe endpoint. Monitors health of background thread.              |
| `/ready`                    | GET  |       | Readiness probe endpoint.                                                   |
| `/transactions`             | POST | 🔒    | Submits a transaction to be appended to the ledger.                         |
| `/transactions/<accountid>` | GET  | 🔒    | Return the account transaction list if authenticated to access the account. |
| `/version`                  | GET  |       | Returns the contents of `$VERSION`                                          |

### Environment Variables

Located in `init/ledgermonolith.env`

- Required
  - `VERSION`
    - a version string for the service
  - `PORT`
    - the port for the webserver
  - `JVM_OPTS`
    - settings for the JVM. Used to obey container memory limits
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret
  - `POSTGRES_DB`
    - URL of the service
  - `POSTGRES_USER`
    - username for the database
  - `POSTGRES_PASSWORD`
    - password for the database
  - `SPRING_DATASOURCE_URL`
    - URL of the database service
  - `SPRING_DATASOURCE_USERNAME`
    - username for the database
  - `SPRING_DATASOURCE_PASSWORD`
    - password for the database
  - `USE_DEMO_DATA`
    - Set to "True" to initialize the bank ledger with demo data
- Optional
  - `POLL_MS`
    - the number of milliseconds to wait in between polls to the database
    - optional. Defaults to 100
  - `CACHE_SIZE`
    - the max number of HTTP requests to cache
    - optional. Defaults to 1,000
  - `CACHE_MINUTES`
    - the expiry time for the cache in minutes
    - optional. Defaults to 60
  - `HISTORY_LIMIT`
    - the number of past transactions to store for each user
    - optional. Defaults to 100
  - `EXTRA_LATENCY_MILLIS`
    - add fake extra latency in milliseconds to transaction history requests
    - optional. Defaults to 0

### Scripts

- `scripts/deploy-monolith.sh`: deploys service to a VM on Google Compute Engine
- `scripts/teardown-monolith.sh`: teardown service from Google Compute Engine
- `scripts/build-artifacts.sh`: pushes build artifacts to Google Cloud Storage
- `scripts/delete-artifacts.sh`: deletes build artifacts in Google Cloud Storage

## Quickstart

To deploy Bank of Anthos with a monolith service:

```
# In the root directory of the project repo
export PROJECT_ID=<your-project-id>
export ZONE=<your-gcp-zone>
make cluster && \
make monolith-fw-rule && \
make monolith
```

Deploys the full Bank of Anthos application with a Java monolith service running
on a Google Compute Engine VM and all other microservices running on Kubernetes.

## Deploying the Monolith

### Option 1 - From Canonical Artifacts

Deploy the canonical version of the monolith to a Google Compute Engine VM.
Use canonical build artifacts hosted on Google Cloud Storage at
`gs://bank-of-anthos-ci/monolith`.

```
# In the root directory of the project repo
export PROJECT_ID=<your-project-id>
export ZONE=<your-gcp-zone>
make monolith-deploy
```

### Option 2 - With Custom-built Artifacts

Deploy a custom version of the monolith to a Google Compute Engine VM.
Compile and build artifacts locally and push them to Google Cloud Storage (GCS).

Specify the GCS location with environment variable `GCS_BUCKET`.
Artifacts will be pushed to `gs://{GCS_BUCKET}/monolith`.

```
# In the root directory of the project repo
export PROJECT_ID=<your-project-id>
export ZONE=<your-gcp-zone>
export GCS_BUCKET=<your-gcs-bucket>
make monolith-build
make monolith-deploy
```

## Checking the Monolith

### Startup Script Logs

The output of the monolith VM startup procedure is logged.

1. Go to the [Google Compute Engine instances page](https://cloud.google.com/compute/instances).
2. Select `View logs` under the `...` options button for the monolith VM: `ledgermonolith-service`.
3. Search for "startup-script" in the search bar of the Logs Viewer.

### App Build Artifacts

Build artifacts for the monolith VM should be saved to `/opt/monolith`.

1. Go to the [Google Compute Engine instances page](https://cloud.google.com/compute/instances).
2. Click the `SSH` button on the monolith VM: `ledgermonolith-service`.
3. Enter `ls /opt/monolith` in the shell prompt.

### Java App Logs

Runtime logs for the java app are piped to `/var/log/monolith.log`.

1. Go to the [Google Compute Engine instances page](https://cloud.google.com/compute/instances).
2. Click the `SSH` button on the monolith VM: `ledgermonolith-service`.
3. Enter `tail -f /var/log/monolith.log` in the shell prompt.

### Serving HTTP Requests

The monolith service can be queried via HTTP from a client on the same Google
Cloud network that also has the `monolith` network tag.

1. Go to the [Google Compute Engine instances page](https://cloud.google.com/compute/instances).
2. Note the internal ip address of the monolith VM: `ledgermonolith-service`.
3. Create a VM instance on the monolith network - `default` - and add the network tag `monolith`.
4. Click the `SSH` button on the instance after it has successfully started.
5. Enter `curl ledgermonolith-service.c.[PROJECT_ID].internal:8080/version` in the shell prompt, replacing PROJECT_ID with your GCP project id.
6. If you see a version string like `v#.#.#`, the ledgermonolith is correctly serving HTTP requests

## Running Bank of Anthos with the Monolith

To run the full Bank of Anthos application you also need to configure and deploy
the microservices that are not part of the ledgermonolith service.
This directory (`src/ledgermonolith`) includes a custom `config.yaml` file.
The `config.yaml` along with the associated manifests in the `kubernetes-manifests`
directory located in the repository's root folder will deploy the other supporting
microservices (including the frontend), plus the accounts database.
To deploy, run the following commands from this directory:

1. Set environment variables

```
CLUSTER=<your-cluster-name>
PROJECT_ID=<your-project-id>
ZONE=<your-gcp-zone>
```

2. Create a GKE cluster.

```
gcloud container clusters create ${CLUSTER} \
  --machine-type=e2-standard-4 \
  --num-nodes=4 \
  --project=${PROJECT_ID} \
  --subnetwork=default \
  --zone=${ZONE}
```

3. Create a firewall rule to allow the cluster to talk to the monolith.

```
CLUSTER_POD_CIDR=$(gcloud container clusters describe ${CLUSTER} --format="value(clusterIpv4Cidr)" --project ${PROJECT_ID} --zone=${ZONE}) && \
gcloud compute firewall-rules create monolith-gke-cluster \
  --allow TCP:8080 \
  --project=${PROJECT_ID} \
  --source-ranges ${CLUSTER_POD_CIDR} \
  --target-tags monolith
```

4. Replace `[PROJECT_ID]` with your `$PROJECT_ID` in `src/ledgermonolith/config.yaml`.

5. Get credentials for the cluster

```
gcloud container clusters get-credentials ${CLUSTER} \
  --project=${PROJECT_ID} \
  --zone ${ZONE}
```

6. Run the following commands from the root of this repository, to deploy your custom config alongside the other Bank of Anthos services.

```
kubectl apply -f src/ledgermonolith/config.yaml
kubectl apply -f extras/jwt/jwt-secret.yaml
kubectl apply -f kubernetes-manifests/accounts-db.yaml
kubectl apply -f kubernetes-manifests/userservice.yaml
kubectl apply -f kubernetes-manifests/contacts.yaml
kubectl apply -f kubernetes-manifests/frontend.yaml
kubectl apply -f kubernetes-manifests/loadgenerator.yaml
```
