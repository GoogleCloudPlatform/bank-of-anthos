# Ledger Writer Service

The ledger writer service accepts and validates incoming transactions before writing them to the ledger.

Implemented in Java with Spring Boot.

### Endpoints

| Endpoint           | Type  | Auth? | Description                                          |
| ------------------ | ----- | ----- | ---------------------------------------------------- |
| `/ready`           | GET   |       |  Readiness probe endpoint.                           |
| `/transactions`    | POST  | 🔒    |  Submits a transaction to be appended to the ledger. |
| `/version`         | GET   |       |  Returns the contents of `$VERSION`                  |

### Environment Variables

- `VERSION`
  - a version string for the service
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
- `BALANCES_API_ADDR`
  - the address and port of the `balancereader` service
- `PUB_KEY_PATH`
  - the path to the JWT signer's public key, mounted as a secret
- `JVM_OPTS`
  - settings for the JVM. Used to obey container memory limits

### Kubernetes Resources

- [deployments/ledgerwriter](/kubernetes-manifests/ledger-writer.yaml)
- [service/ledgerwriter](/kubernetes-manifests/ledger-writer.yaml)
