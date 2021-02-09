# Using Bank of Anthos with an Opsani DevTrial account

1. Deploy the Bank of Anthos application (see the instructions and helper scripts in the /opsani directory)
2. Install the Dev Trial application as defined in the Dev Trial README that you either received from your Opsani engineering contact, or downloaded from your https://console.opsani.com account and application servo page.

## OR Ignore that, and use these scripts along with the opsani-manifest.yaml from the DevTrial "bundle"

The opsani-manifest.yaml document has four parameters that need to be appropriately configured in the opsani-manifest.yaml:

* NAMESPACE: The namespace against which the opsani servo is configured (default: bank-of-anthos-opsani)
* DEPLOYMENT: The Kubernetes deployment name that is to be optimized (default: frontend)
* CONTAINER: The name of the container in the Deployment spec that will be optimized (default: front)
* SERVICE: The Kubernetes service that points to the deployment application components (default: frontend)

A helper file that can be sourced in a `bash` environment (e.g. `source bank-of-anthos.source`) will create environment variables that will simplify the fine tuning of the Dev Trial environment to the Bank of Anthos application. It is recommended that any changes you may have made to the app, or the namespace, be captured in this file and then execute the following command (on a bash command line)

```sh
source bank-of-anthos.source
```

The default cpu and memory parameters and optimization steps that are in the default Dev Trial manifest are appropraite for the Bank of Anthos application, so the only changes that need to be made manually are the replacement of the four parameters described above.

If you haven't already, copy the opsani-manifests.yaml document from the servo_install folder that was extracted from the DevTrial bundle, and only if you are not using the default parameters, modify the file with the parameters in the bank-of-anthos.source file, and then run this helper script to replace the parameters in the opsani-manifests.yaml document (don't worry, we'll create a backup for you):

```sh
update-opsani-manifest.sh
```

## Install the opsani servo via the opsani-manifests.yaml document
  
```sh
kubectl apply -n ${NAMESPACE:-bank-of-anthos-opsani} -f opsani-manifests.yaml

```

In addition, there are a few additional annotations and labels required, and we will want Opsani's servo to inject the envoy sidecar into the target Deployment under optimization. you can run the inject-sidecar.sh script to enable these modifications, or follow the output of the servo log from the servo deployment.

## Envoy sidecar injection.

If you follow the Dev trials README document, you will be asked to look at the log output of servo. This will guide you through the steps needed to get envoy injected and working properly.  The following helper scripts support injecting the envoy, and will also update the service port mapping once envoy is injected.  You can also run the steps in the script manually, and then update the service remapping manually.

### Inject Envoy

```sh
./inject-sidecar.sh
```

### Eject Envoy

```sh
./eject-sidecar.sh
```

### Service port remapping

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

## Clean-up the enviornment (e.g. back to application only)

To get back to a "generic" Bank-of-Anthos application with no Opsani elements, run the eject script, and then remove the services and configurations added for servo:

```sh
./eject-sidecar.sh
kubectl delete -f opsani-manifests.yaml
```
