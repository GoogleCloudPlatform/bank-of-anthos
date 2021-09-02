# Kustomize the Bank-of-Anthos application for envoy injection

## Deployment

The envoy-patch adds an envoy container and annontations to allow prometheus to discover and scrape thie application enviornment

## Service

The service patch patches the service  to point to the newly added envoy resource.  the frontend component exposes it's service on port 80, so uses a slightly modified patch.

## Application

If you already applied the "bank-of-anthos" app with the opsani/deploy.sh script, you should be able to apply an update in the main bank-of-anthos directory with:

```sh
kubectl apply -k envoy/
```

Otherwise, if you have yet to deploy the Bank-of-Anthos app, deploy with the `deploy-envoy.sh` script:

```sh
cd opsani
./deploy-envoy.sh
```
