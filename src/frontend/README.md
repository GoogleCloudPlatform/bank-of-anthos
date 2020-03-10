# Frontend Service

The frontend service manages the user-facing web interface for the application.

Implemented in Python with Flask.

### Endpoints

| Enndpoint  | Type  | JWT Required | Description                                                                               |
| ---------- | ----- | ------------ | ----------------------------------------------------------------------------------------- |
| `/version` | GET   |              |  Returns the contents of `$VERSION`                                                       |
| `/ready`   | GET   |              |  Readiness probe endpoint.                                                                |
| `/home`    | GET   | 🔒           |  Renders homepage if authenticated Otherwise redirects to `/login`                        |
| `/login`   | GET   |              |  Renders login page if not authenticated. Otherwise redirects to `/home`                  |
| `/login`   | POST  |              |  Submits login request to `userservice`                                                   |
| `/signup`  | GET   |              |  Renders signup page if not authenticated. Otherwise redirects to `/home`                 |
| `/login`   | POST  |              |  Submits new user signup request to `userservice`                                         |
| `/`        | GET   | 🔒           |  Renders `/home` or `/login` based on authentication status. Must always return 200        |
| `/payment` | POST  | 🔒           |  Submits a new internal payment transaction to `ledgerwriter`                             |
| `/deposit` | POST  | 🔒           |  Submits a new external deposit transaction to `ledgerwriter`                             |
| `/logout`  | POST  | 🔒           | delete local authentication token and redirect to `/login`                                |

### Environment Variables

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver
- `TRANSACTIONS_API_ADDR`
  - the address and port of the `ledgerwriter` service
- `BALANCES_API_ADDR`
  - the address and port of the `balancereader` service
- `HISTORY_API_ADDR`
  - the address and port of the `transactionhistory` service
- `CONTACTS_API_ADDR`
  - the address and port of the `contacts` service
- `USERSERVICE_API_ADDR`
  - the address and port of the `userservice`
- `LOCAL_ROUTING_NUM`
  - the routing number for our bank
- `PUB_KEY_PATH`
  - the path to the JWT signer's public key, mounted as a secret
- `DEFAULT_USERNAME`
  - a string to pre-populate the "username" field. Optional
- `DEFAULT_PASSWORD`
  - a string to pre-populate the "password" field. Optional

### Kubernetes Resources

- [deployments/frontend](/kubernetes-manifests/frontend.yaml)
- [service/frontend](/kubernetes-manifests/frontend.yaml)
