# Accounts Database Service

The `accounts-db` service holds all user data for the system.

The container is a standard MongoDB image, with a default database added on top.
By default, `accounts-db` creates a single in-memory replica.

implemented using MongoDB.

### Kubernetes Resources

- [deployments/accounts-db](/kubernetes-manifests/accounts-db.yaml)
- [service/accounts-db](/kubernetes-manifests/accounts-db.yaml)
