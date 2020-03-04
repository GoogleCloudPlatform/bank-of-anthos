# Ledger Database Service

The `ledger-db` service is an append-only ledger that acts as the source of truth
for all transaction data.

The container is a standard redis image, with an added script to insert some
default transaction data on first launch.

implemented using Redis Streams.

### Environment Variables

- `USE_DEFAULT_DATA`
  - if adds default data to ledger when initialized if `True`
- `LOCAL_ROUTING_NUM`
  - the routing number for our bank
- `DEFAULT_ACCOUNT`
  - the default user account to generate transactions for if `USE_DEFAULT_DATA` is `True`
- `DEFAULT_DEPOSIT_ACCOUNT`
  - the account number for the external bank account initiating deposits in default data
- `DEFAULT_DEPOSIT_ROUTING`
  - the routing number for the external bank account initiating deposits in default data

### Kubernetes Resources

- [deployments/ledger-db](/kubernetes-manifests/ledger-db.yaml)
- [service/ledger-db](/kubernetes-manifests/ledger-db.yaml)
