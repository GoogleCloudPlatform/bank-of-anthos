# Ledger Monolith Service

The ledger monolith service reads and writes transactions belonging to the bank ledger as stored in the `ledger-db`.

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

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver
- `POLL_MS`
  - the number of milliseconds to wait in between polls to `ledger-db`
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
- `JVM_OPTS`
  - settings for the JVM. Used to obey container memory limits
- `EXTRA_LATENCY_MILLIS`
  - add fake extra latency in milliseconds to transaction history requests

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret

- ConfigMap `service-api-config`
  - `BALANCES_API_ADDR`
    - the address and port of the `balancereader` service

- ConfigMap `ledger-db-config`:
  - `SPRING_DATASOURCE_URL`
    - URL of the `ledger-db` service
  - `SPRING_DATASOURCE_USERNAME`
    - username for the `ledger-db` database
  - `SPRING_DATASOURCE_PASSWORD`
    - password for the `ledger-db` database

