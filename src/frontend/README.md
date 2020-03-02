# Frontend Service

The frontend service manages the user-facing web interface for the application.

### Language
Python

### Endpoints

| Enndpoint  | Type  | JWT Required | Description                                                                               |
| ---------- | ----- | ------------ | ----------------------------------------------------------------------------------------- |
| /          | GET   | 🔒           |  Renders homepage if authenticated. Otherwise redirects to `/login` (alias for `/home`)   |
| /home      | GET   | 🔒           |  Renders homepage if authenticated. Otherwise redirects to `/login` (alias for `/`        |
| /login     | GET   |              |  Renders login page if not authenticated. Otherwise redirects to `/home`                  |
| /login     | POST  |              |  Submits login request to `userservice`                                                   |
| /signup    | GET   |              |  Renders signup page if not authenticated. Otherwise redirects to `/home`                 |
| /login     | POST  |              |  Submits new user signup request to `userservice`                                         |
| /payment   | POST  | 🔒           |  Submits a new internal payment transaction to `ledgerwriter`                             |
| /deposit   | POST  | 🔒           |  Submits a new external deposit transaction to `ledgerwriter`                             |
| /logout    | POST  | 🔒           | delete local authentication token and redirect to `/login`                                |


### Kubernetes

Resources:
  - [deployments/frontend](/kubernetes-manifests/frontend.yaml)
  - [service/frontend](/kubernetes-manifests/frontend.yaml)
