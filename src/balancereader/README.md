# Balance Reader Service

The balance reader service provides efficient readable cache of user balances, as read from ledger.

The `ledger-db` service holds the source of truth for the system. The `balance-reader` returns data on a
best-effort basis, but may be out of date when under heavy load.

Implemented in Java with Spring Boot.

### Endpoints

| Enndpoint      | Type  | JWT Required | Description                                                     |
| -------------- | ----- | ------------ | --------------------------------------------------------------- |
| `/ready`       | GET   |              |  Readiness probe endpoint.                                      |
| `/healthy`     | GET   |              |  Liveness probe endpoint. Monitors health of background thread. |
| `/get_balance` | POST  | 🔒           |  Returns the total balance of the authenticated user.           |

### Environment Variables

- `LEDGER_ADDR`
  - the address of the `ledger-db` service
- `LEDGER_PORT`
  - the port of the `ledger-db` service
- `LEDGER_STREAM`
  - the Redis Stream name used for the ledger
- `PORT`
  - the port for the webserver
- `LOCAL_ROUTING_NUM`
  - the routing number for our bank
- `PUB_KEY_PATH`
  - the path to the JWT signer's public key, mounted as a secret
- `JVM_OPTS`
  - settings for the JVM. Used to obey container memory limits

### Kubernetes Resources

- [deployments/balancereader](/kubernetes-manifests/balance-reader.yaml)
- [service/balancereader](/kubernetes-manifests/balance-reader.yaml)
