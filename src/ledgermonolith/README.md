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

- `init/ledgermonolith.env`
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

- `scripts/push-artifacts.sh`: pushes build artifacts to Google Cloud Storage
- `scripts/deploy-monolith.sh`: deploys service to a VM on Google Compute Engine
- `scripts/teardown-monolith.sh`: teardown the service from Google Cloud

## Deploying Manually

### Make

```
# In the root directory of the project repo
PROJECT_ID=<your-project-id>
ZONE=<your-gcp-zone>
make monolith
```

### Bash

```
# In the root directory of the project repo
PROJECT_ID=<your-project-id>
ZONE=<your-gcp-zone>
./src/ledgermonolith/scripts/push-artifacts.sh
./src/ledgermonolith/scripts/deploy-monolith.sh
```
