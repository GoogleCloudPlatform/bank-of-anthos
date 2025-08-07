# Adding a new microservice

This document outlines the steps required to add a new microservice to the Bank of Anthos application.

## 1. Create a new directory

Create a new directory for your microservice within the `src/` directory. The directory name should be the name of your microservice.

## 2. Add source code

Place your microservice's source code inside the newly created directory. The structure of this directory should follow the conventions of the existing microservices. For example, a Python-based service would include at minimum the following files:

- `README.md`: The service's description and documentation.
- `main.py`: The application's entry point.
- `requirements.in`: A list of Python dependencies.
- `Dockerfile`: To containerize the application.
- `skaffold.yaml`: For local development with Skaffold.
- `cloudbuild.yaml`: For continuous integration with Google Cloud Build.

Take a look at existing microservices for inspiration.

## 3. Create a Dockerfile

Create a `Dockerfile` in your microservice's directory. This file will define the steps to build a container image for your service.

Refer to this example and tweak based on your new service's needs: https://github.com/GoogleCloudPlatform/bank-of-anthos/blob/main/src/frontend/Dockerfile

## 4. Create a `cloudbuild.yaml` file

Create a `cloudbuild.yaml` file to configure Google Cloud Build for your microservice. This file specifies the build steps, such as building the Docker image and pushing it to a container registry.

Refer to this example and tweak based on your new service's needs: https://github.com/GoogleCloudPlatform/bank-of-anthos/blob/main/src/frontend/cloudbuild.yaml

## 5. Create a `skaffold.yaml` file

Create a `skaffold.yaml` file to enable local development with [Skaffold](https://skaffold.dev/). This file should define how Skaffold builds and deploys your microservice to a local or remote Kubernetes cluster.

Refer to this example and tweak based on your new service's needs: https://github.com/GoogleCloudPlatform/bank-of-anthos/blob/main/src/frontend/skaffold.yaml

## 6. Create Kubernetes manifests

Create a new directory called `k8s/` in your microservice's directory. Inside this directory, add the necessary Kubernetes YAML files for your new microservice. This typically includes:

- A **Deployment** to manage your service's pods.
- A **Service** to expose your microservice to other services within the cluster.

Ensure you follow the existing naming conventions and that the container image specified in the Deployment matches the one built by your `cloudbuild.yaml` and `skaffold.yaml` files.

Refer to this example and tweak based on your new service's needs: https://github.com/GoogleCloudPlatform/bank-of-anthos/tree/main/src/frontend/k8s

## 7. Update the root `skaffold.yaml`

Add a new module for your microservice to the main `skaffold.yaml` file in the root directory. This allows Skaffold to manage your new service alongside the existing ones.

The file is available here: https://github.com/GoogleCloudPlatform/bank-of-anthos/blob/main/skaffold.yaml

## 8. Update the documentation

Finally, update the project's documentation to reflect the addition of your new microservice. This may include:

- Adding a section to the main `README.md` if the service introduces significant new functionality.
- Updating the architecture diagrams in the `docs/img` directory.
- Adding a new document in the `docs` directory if the service requires detailed explanation.
