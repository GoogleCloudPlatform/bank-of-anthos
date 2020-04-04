# User Service

The user service manages user accounts and authentication. 
It creates and signs JWTs that are used by other services to authenticate users.

Implemented in Python with Flask.

### Endpoints

| Endpoint            | Type  | Auth? | Description                                                      |
| ------------------- | ----- | ----- | ---------------------------------------------------------------- |
| `/login`            | GET   |       |  Returns a JWT if authentication is successful.                  |
| `/ready`            | GET   |       |  Readiness probe endpoint.                                       |
| `/users`            | POST  |       |  Validates and creates a new user record.                        |
| `/version`          | GET   |       |  Returns the contents of `$VERSION`                              |

### Environment Variables

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver
- `ACCOUNTS_DB_URI`
  - the complete URI for the `accounts-db` database
- `TOKEN_EXPIRY_SECONDS`
  - how long JWTs are valid before forcing user logout
- `PRIV_KEY_PATH`
  - the path to the private key for JWT signing, mounted as a secret
- `PUB_KEY_PATH`
  - the path to the public key for JWT signing, mounted as a secret
- `LOG_LEVEL`
  - the [logging level](https://docs.python.org/3/library/logging.html#levels) (default: INFO)

### Kubernetes Resources

- [deployments/userservice](/kubernetes-manifests/userservice.yaml)
- [service/userservice](/kubernetes-manifests/userservice.yaml)
