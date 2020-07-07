# Balance Reader Service

The balance reader service provides an efficient readable cache of user balances, as read from the `ledger-db`.

The `ledger-db` service holds the source of truth for the system.
The `balance-reader` reads and caches data from the `ledger-db`, but may be out of date when under heavy load.

Implemented in Java with Spring Boot and Guava.

### Endpoints

| Endpoint                | Type  | Auth? | Description                                                             |
| ----------------------- | ----- | ----- | ----------------------------------------------------------------------- |
| `/balances/<accountid>` | GET   | 🔒    |  Get the account balance iff owned by the currently authenticated user. |
| `/healthy`              | GET   |       |  Liveness probe endpoint. Monitors health of background thread.         |
| `/ready`                | GET   |       |  Readiness probe endpoint.                                              |
| `/version`              | GET   |       |  Returns the contents of `$VERSION`                                     |

### Environment Variables

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver
- `POLL_MS`
  - the number of milliseconds to wait in between polls to `ledger-db`
  - optional. Defaults to 100
- `CACHE_SIZE`
  - the max number of account balances to store in the cache
  - optional. Defaults to 1,000,000
- `JVM_OPTS`
  - settings for the JVM. Used to obey container memory limits
- `LOG_LEVEL`
  - service level [log level](https://logging.apache.org/log4j/2.x/manual/customloglevels.html)

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret

- ConfigMap `ledger-db-config`:
  - `SPRING_DATASOURCE_URL`
    - URL of the `ledger-db` service
  - `SPRING_DATASOURCE_USERNAME`
    - username for the `ledger-db` database
  - `SPRING_DATASOURCE_PASSWORD`
    - password for the `ledger-db` database

### Kubernetes Resources

- [deployments/balancereader](/kubernetes-manifests/balance-reader.yaml)
- [service/balancereader](/kubernetes-manifests/balance-reader.yaml)
