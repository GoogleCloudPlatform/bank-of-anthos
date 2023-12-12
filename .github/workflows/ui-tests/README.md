# E2E tests

End-to-end tests use the [Cypress](https://cypress.io) test runner.

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

Tests can be filtered by file by passing in files using the `--spec` flag.  Test files are mounted as volumes to Docker, so the test files should be referenced to their relative location with the path prefix of `cypress/integration/`

#### Makefile

All Cypress flags should be passed through the variable `E2E_FLAGS` as a single string.

```console
make test-e2e E2E_FLAGS="--spec cypress/integration/<test-file>.js"
```

#### Docker

```console
docker run -it -v ${E2E_PATH}:/e2e -w /e2e \
 -e CYPRESS_baseUrl=${E2E_URL} -e CYPRESS_CI=false \
 cypress/included:5.0.0 --spec cypress/integration/<test-file>.js
```

### Filtering tests with `.only()` and `.skip()`

The `.only()` and `.skip()` functions can be appended to either single tests or blocks of test. [Read more about them here](https://docs.cypress.io/guides/core-concepts/writing-and-organizing-tests.html#Excluding-and-Including-Tests).

### Screenshots

Failing tests will store screenshots in the `cypress/screenshots` directory (locally and CI) and uploaded as an [artifact to Github Actions](https://docs.github.com/en/actions/guides/storing-workflow-data-as-artifacts) after a failing build. These are helpful when debugging tests.  [Read more about them here](https://docs.cypress.io/guides/guides/screenshots-and-videos.html#Screenshots).
