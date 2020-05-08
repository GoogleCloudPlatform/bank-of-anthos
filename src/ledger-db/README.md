# Ledger Database Service

The `ledger-db` service is an append-only ledger that acts as the source of truth
for all transaction data.

The container is a standard `postgres` image, with an added script to insert some
default transaction data on first launch.

Implemented using Postgres.

### Environment Variables

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank

- ConfigMap `demo-data-config`:
  - `USE_DEMO_DATA`
    - adds demo transaction data to the ledger when initialized if `True`
    - data is initialized with /src/ledger-db/initdb/1_create_transactions.sh

- ConfigMap `ledger-db-config`:
  - `POSTGRES_DB`
    - database name
  - `POSTGRES_USER`
    - database username
  - `POSTGRES_PASSWORD`
    - database password

### Kubernetes Resources

- [deployments/ledger-db](/kubernetes-manifests/ledger-db.yaml)
- [service/ledger-db](/kubernetes-manifests/ledger-db.yaml)
