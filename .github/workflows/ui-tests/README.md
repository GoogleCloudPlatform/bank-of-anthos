# E2E tests

End-to-end tests use the [Cypress](cypress.io) test runner.

## Prerequisites

1. [BoA Development Guide]((../../../docs/development.md))
    * [Docker Desktop](https://www.docker.com/products/docker-desktop)
    * A working Bank of Anthos deployment
1. Ensure you are authenticated to the correct cluster

    ```console
        gcloud container clusters get-credentials bank-of-anthos --zone us-west1-a
    ```

### Running all tests

Test can be run by using the Makefile or the Docker command line tool.

The [Makefile](../../../Makefile) identifies the exposed IP from the Frontend service and runs the E2E tests against it.

From the project's root, run:

```console
make test-e2e
```

To use the Docker command line tool directly, the test directory and URL must be passed.
From the project's root, run:

```console
E2E_PATH=${PWD}/.github/workflows/ui-tests
E2E_URL=http://$(kubectl get service frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
docker run -it -v ${E2E_PATH}:/e2e -w /e2e -e CYPRESS_baseUrl=${E2E_URL} -e CYPRESS_CI=false cypress/included:4.3.0
```

### Running one test file

Make file:

```console
make test-e2e --spec cypress/integration/<test-file>.js
```

Docker:

```console
docker run -it -v ${E2E_PATH}:/e2e -w /e2e \
 -e CYPRESS_baseUrl=${E2E_URL} -e CYPRESS_CI=false \
 cypress/included:4.3.0 --spec cypress/integration/<test-file>.js
```