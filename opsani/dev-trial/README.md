# Using Bank of Anthos with an Opsani DevTrial account

This README will walk you through how to start optimization with Opsani.

## Prerequisites

1. Bank of Anthos application running in your Kubernetes cluster (if not, see the instructions and helper scripts in the /opsani directory). 

2. `servo_install.tar.gz` archive installed and expanded. To download this, go to https://console.opsani.com or contact Opsani support.

## Installing Opsani

The opsani-manifest.yaml document has four parameters that need to be appropriately configured in the opsani-manifest.yaml:

* NAMESPACE: The namespace against which the opsani servo is configured (default: bank-of-anthos-opsani)
* DEPLOYMENT: The Kubernetes deployment name that is to be optimized (default: frontend)
* CONTAINER: The name of the container in the Deployment spec that will be optimized (default: front)
* SERVICE: The Kubernetes service that points to the deployment application components (default: frontend)

A helper file that can be sourced in a `bash` environment (e.g. `source bank-of-anthos.source`) will create environment variables that will simplify the fine tuning of the Dev Trial environment to the Bank of Anthos application. It is recommended that any changes you may have made to the app, or the namespace, be captured in  `bank-of-anthos.source` file. 

Run the following command:

```sh
source bank-of-anthos.source
```

If you haven't already, copy the opsani-manifests.yaml document from the servo_install folder that was extracted from the DevTrial bundle, and only if you are not using the default parameters, modify the file with the parameters in the bank-of-anthos.source file. 

Run this helper script to replace the parameters in the opsani-manifests.yaml document (don't worry, we'll create a backup for you):

```sh
update-opsani-manifest.sh
```

### Install the Opsani Servo via the opsani-manifests.yaml document
  
```sh
kubectl apply -n ${NAMESPACE:-bank-of-anthos-opsani} -f opsani-manifests.yaml

```

### Envoy sidecar injection.

In addition, there are a few additional annotations and labels required, and we will want Opsani's servo to inject the envoy sidecar into the target Deployment under optimization.

The following helper scripts support injecting the envoy, and will also update the service port mapping once envoy is injected.  You can also run the steps in the script manually, and then update the service remapping manually.


```sh
./inject-sidecar.sh
```

At this point, the Opsani servo should be working and communicating with our optimization engine. Check the https://console.opsani.com to see optimization progress.

## Clean-up the environment (e.g. back to application only)

To get back to a "generic" Bank of Anthos application with no Opsani elements, the simplest step is to run the following:

```sh
./eject-sidecar.sh
kubectl delete -f opsani-manifests.yaml
```
For a manual clean-up, one can use the following commands:

### Eject Envoy

```sh
./eject-sidecar.sh
```

### Service port remapping

The following details how to disable metrics gathering without removing the envoy sidecar.

You can use the `update-svc.sh` script to redirect the service to the envoy port (9980 by default) or back directly to the app (8080 in most cases by default). This is the quickest way to "remove" the envoy sidecar from the application, as it will direct traffic directly back to the application for both the main and tuning instance (which is simply another replica of the main component under optimization)

```sh
./update-svc.sh ${SERVICE} ${PORT}
```

Commonly this would be:

```sh
./update-svc.sh ${SERVICE} 9980
```

or to remove the envoy metrics capture from the forwarding path:

```sh
./update-svc.sh ${SERVICE} 8080
```
