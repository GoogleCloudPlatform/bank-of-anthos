# UI Tests

Frontend tests use [Cypress](cypress.io).


## Running Tests Locally

Update `baseUrl` in [cypress.json](cypress.json) to url you are testing against.

Run [cypress/included:4.3.0](https://github.com/cypress-io/cypress-docker-images/tree/master/included/4.3.0) from command line

```console
docker run -it -v $PWD:/e2e -w /e2e cypress/included:4.3.0
```

