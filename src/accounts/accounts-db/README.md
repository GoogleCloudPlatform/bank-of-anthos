# Accounts Database Service

The `accounts-db` service stores bank user account data.

The container base is a standard PostgreSQL image. On startup, it initializes
a database schema and loads test data using the scripts located in the `initdb/`
directory.

To access the default test user account, specify the appropriate environment
variables listed below. You may login to the account using the password
`password`.

### Environment Variables

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank

- ConfigMap `demo-data-config`:
  - `USE_DEMO_DATA`
    - adds demo user accounts to the database when initialized if `True`
    - data is initialized with /src/accounts-db/initdb/1_load_testdata.sh

- ConfigMap `accounts-db-config`:
  - `POSTGRES_DB`
    - database name
  - `POSTGRES_USER`
    - database username
  - `POSTGRES_PASSWORD`
    - database password

### Kubernetes Resources

- [deployments/accounts-db](/kubernetes-manifests/accounts-db.yaml)
- [service/accounts-db](/kubernetes-manifests/accounts-db.yaml)
