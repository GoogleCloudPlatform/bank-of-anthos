# TLS Frontend with Self-Signed Certificates

This directory contains manifests for deploying the Bank of Anthos frontend with an HTTPS-only ingress, using self-signed certificates and a global static IP.

## Prerequisites

- openssl tool
- A GCP project
- 1 GKE cluster

> Note: Ensure you have created the cluster and set your `kubectl` context to use that specific cluster's configuration before running the following commands

## Setup

1. Set the PROJECT_ID variable.

```
export PROJECT_ID="your-project-id"
```

2. Run the `./setup.sh` script. This generates the self-signed certs, creates a static IP in your project, deploys the Bank of Anthos app to your cluster, and configures the frontend `Ingress` resource, along with a `FrontendConfig` that enforces an HTTP->HTTPS redirect.

```
./setup.sh
```

3. Visit your global static IP (`ADDRESS` field below). This should route to the frontend UI with HTTPS.
> Note: Since the setup uses a self-signed certificate your browser might warn you about it. You will have to accept it as an exception.

```
kubectl get ingress frontend-ingress
```

Expected output:

```
NAME               CLASS    HOSTS   ADDRESS        PORTS     AGE
frontend-ingress   <none>   *       34.120.196.3   80, 443   18m
```
