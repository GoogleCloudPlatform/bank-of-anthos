# Load Generator Service

The load generator continuously sends requests imitating users to the frontend service.
Pages are loaded, new accounts are periodically created, and transactions between accounts are created.

Implemented in Python with Locust.

### Load Generator Tasks

- view_login
  - load the `/login` page
- view_signup
  - load the `/signup` page
- signup
  - sends POST request to `/signup` to create a new user
- view_index
  - load the `/home` page
- view_home
  - load the / page
- payment
  - POST to `/payment`, sending money to other account
- deposit
  - POST to `/deposit`, depositing external money into account
- login
  - sends POST request to `/login` with stored credentials
- logout
  - sends a `/logout` POST request

### Environment Variables

- `FRONTEND_ADDR`
  - the address and port of the `frontend` service
- `USERS`
  - The number of concurrent users to simulate
- `LOG_LEVEL`
  - The [logging level](https://docs.python.org/3/library/logging.html#levels) (default: INFO)

### Kubernetes Resources

- [deployments/loadgenerator](/kubernetes-manifests/loadgenerator.yaml)
- [service/loadgenerator](/kubernetes-manifests/loadgenerator.yaml)
