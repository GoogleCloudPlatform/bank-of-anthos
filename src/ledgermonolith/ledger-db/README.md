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

- ConfigMap `default-data-config`:
  - `USE_DEFAULT_DATA`
    - adds default transaction data to the ledger when initialized if `True`
    - configure default data in /kubernetes-manifests/default-data-config.yaml 

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
