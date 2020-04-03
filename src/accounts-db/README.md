# Accounts Database Service

The `accounts-db` service stores bank user account data.

The container base is a standard PostgreSQL image. On startup, it initializes
a database schema and loads test data using the scripts located in the `initdb/`
directory.

To access the default test user account, specify the appropriate environment
variables listed below. You may login to the account using the password
`password`.

### Environment Variables

- `TEST_USERNAME`
  - the username of the default test account to initialize
- `TEST_ACCOUNTID`
  - the accountid of the default test account to initialize
- `LOCAL_ROUTING_NUM`
  - the routing number for this bank

### Kubernetes Resources

- [deployments/accounts-db](/kubernetes-manifests/accounts-db.yaml)
- [service/accounts-db](/kubernetes-manifests/accounts-db.yaml)
