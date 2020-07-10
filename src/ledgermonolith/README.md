# Ledger Monolith Service

Reads and writes transactions belonging to the bank ledger.

Implemented in Java with Spring Boot and Guava.

### Endpoints

| Endpoint                    | Type  | Auth? | Description                                                                   |
| --------------------------- | ----- | ----- | ----------------------------------------------------------------------------- |
| `/balances/<accountid>`     | GET   | 🔒    |  Get the account balance iff owned by the currently authenticated user. |
| `/healthy`                  | GET   |       |  Liveness probe endpoint. Monitors health of background thread.               |
| `/ready`                    | GET   |       |  Readiness probe endpoint.                                                    |
| `/transactions`             | POST  | 🔒    |  Submits a transaction to be appended to the ledger. |
| `/transactions/<accountid>` | GET   | 🔒    |  Return the account transaction list iff authenticated to access the account. |
| `/version`                  | GET   |       |  Returns the contents of `$VERSION`                                           |

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
  - `BALANCES_API_ADDR`
    - the address and port of the `balancereader` service
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
- `scripts/push-artifacts.sh`: pushes build artifacts to Google Cloud Storage
- `scripts/delete-artifacts.sh`: deletes build artifacts in Google Cloud Storage

## Deploying

### From Canonical Artifacts

Deploy the canonical version of the monolith to a Google Compute Engine VM.
Use canonical build artifacts hosted on Google Cloud Storage at
`gs://bank-of-anthos/monolith`.

#### Make

```
# In the root directory of the project repo
PROJECT_ID=<your-project-id>
ZONE=<your-gcp-zone>
make deploy-monolith
```

#### Bash

```
# In the root directory of the project repo
PROJECT_ID=<your-project-id>
ZONE=<your-gcp-zone>
./src/ledgermonolith/scripts/deploy-monolith.sh
```

### With Custom-built Artifacts

Deploy a custom version of the monolith to a Google Compute Engine VM.
Compile and build artifacts locally and push them to Google Cloud Storage (GCS).

Specify the GCS location with environment variable `GCS_BUCKET`.
Artifacts will be pushed to `gs://{GCS_BUCKET}/monolith'.

#### Make

```
# In the root directory of the project repo
PROJECT_ID=<your-project-id>
ZONE=<your-gcp-zone>
GCS_BUCKET=<your-gcs-bucket>
make monolith
make deploy-monolith
```

#### Bash

```
# In the root directory of the project repo
PROJECT_ID=<your-project-id>
ZONE=<your-gcp-zone>
GCS_BUCKET=<your-gcs-bucket>
./src/ledgermonolith/scripts/push-artifacts.sh
./src/ledgermonolith/scripts/deploy-monolith.sh
```
