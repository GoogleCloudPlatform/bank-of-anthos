# Frontend Service

The frontend service manages the user-facing web interface for the application.

Implemented in Typescript with Angular.

### Endpoints

### Environment Variables

- `VERSION`
  - a version string for the service
- `DEFAULT_USERNAME`
  - a string to pre-populate the "username" field. Optional
- `DEFAULT_PASSWORD`
  - a string to pre-populate the "password" field. Optional

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret

### Kubernetes Resources

- [deployments/frontend](/kubernetes-manifests/frontend.yaml)
- [service/frontend](/kubernetes-manifests/frontend.yaml)