# Frontend Service

The frontend service manages the user-facing web interface for the application.

Implemented in Python with Flask.

### Endpoints

| Endpoint   | Type  | Auth? | Description                                                                               |
| ---------- | ----- | ----- | ----------------------------------------------------------------------------------------- |
| `/`        | GET   | 🔒    |  Renders `/home` or `/login` based on authentication status. Must always return 200       |
| `/deposit` | POST  | 🔒    |  Submits a new external deposit transaction to `ledgerwriter`                             |
| `/home`    | GET   | 🔒    |  Renders homepage if authenticated Otherwise redirects to `/login`                        |
| `/login`   | GET   |       |  Renders login page if not authenticated. Otherwise redirects to `/home`                  |
| `/login`   | POST  |       |  Submits login request to `userservice`                                                   |
| `/logout`  | POST  | 🔒    | delete local authentication token and redirect to `/login`                                |
| `/payment` | POST  | 🔒    |  Submits a new internal payment transaction to `ledgerwriter`                             |
| `/ready`   | GET   |       |  Readiness probe endpoint.                                                                |
| `/signup`  | GET   |       |  Renders signup page if not authenticated. Otherwise redirects to `/home`                 |
| `/signup`  | POST  |       |  Submits new user signup request to `userservice`                                         |
| `/version` | GET   |       |  Returns the contents of `$VERSION`                                                       |

### Environment Variables

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver
- `SCHEME`
  - the URL scheme to use on redirects (http or https)
- `DEFAULT_USERNAME`
  - a string to pre-populate the "username" field. Optional
- `DEFAULT_PASSWORD`
  - a string to pre-populate the "password" field. Optional
- `BANK_NAME`
  - a string that will be shown in the navbar to indicate the name of the bank. Optional, defaults to `Bank of Anthos`
- `CYMBAL_LOGO`
  - boolean, set to `true` to toggle the CymbalBank logo and name. Defaults to `false`.
- `ENV_PLATFORM`
  - a string to customize the platform banner depending on where application is running. Available options [alibaba, aws, azure, gcp, local, onprem]

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret

- ConfigMap `service-api-config`:
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

### Kubernetes Resources

- [deployments/frontend](/kubernetes-manifests/frontend.yaml)
- [service/frontend](/kubernetes-manifests/frontend.yaml)
