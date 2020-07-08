# Accounts Monolith Service

The user service endpoints manages user accounts and authentication.
It creates and signs JWTs that are used by other services to authenticate users.
The contacts service endpoints  stores a list of saved accounts associated with a user.
Data from the contacts service endpoints is used for drop down in "Send Payment" and "Deposit" forms.

Implemented in Python with Flask.

### Endpoints

| Endpoint                | Type  | Auth? | Description                                                      |
| ----------------------- | ----- | ----- | ---------------------------------------------------------------- |
| `/login`                | GET   |       |  Returns a JWT if authentication is successful.                  |
| `/users`                | POST  |       |  Validates and creates a new user record.                        |
| `/contacts/<username>`  | GET   | 🔒    |  Retrieve a list of saved accounts for the authenticated user.   |
| `/contacts/<username>`  | POST  | 🔒    |  Add a new saved account for the authenticated user.             |
| `/ready`                | GET   |       |  Readiness probe endpoint.                                       |
| `/version`              | GET   |       |  Returns the contents of `$VERSION`                              |

### Environment Variables

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver (default: 8080)
- `PRIV_KEY_PATH`
  - the path to the private key for JWT signing, mounted as a secret
- `TOKEN_EXPIRY_SECONDS`
  - how long JWTs are valid before forcing user logout (default:3600)
- `LOG_LEVEL`
  - the service-specific [logging level](https://docs.python.org/3/library/logging.html#levels) (default: INFO)

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret

- ConfigMap `accounts-db-config`:
  - `ACCOUNTS_DB_URI`
    - the complete URI for the `accounts-db` database

### Kubernetes Resources

- [deployments/accountsservice](/kubernetes-manifests/accountsservice.yaml)
- [service/accountsservice](/kubernetes-manifests/accountsservice.yaml)