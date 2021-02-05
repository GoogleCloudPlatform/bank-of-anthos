# Using Bank of Anthos with an Opsani DevTrial account

1. Deploy the Bank of Anthos application (see the instructions and helper scripts in the /opsani directory)
2. Install the Dev Trial application as defined in the Dev Trial README that you either received from your Opsani engineering contact, or downloaded from your https://console.opsani.com account and application servo page.

## Install

As described in the Opsani Dev Trial documentation, there are four parameters that need to be appropriately configured in the opsani-manifest.yaml:

* NAMESPACE: should match the namespace against which the opsani servo is configured (default: bank-of-anthos-opsani)
* DEPLOYMENT:  Is the Kubernetes deployment name that is to be optimized (default: frontend)
* SERVICE: Is the Kubernetes service that points to the deployment application components (default: frontend)
* CONTAINER: Is the name of the container in the Deployment spec that will be optimized (default: front)

A helper file that can be sourced in a `bash` environment (e.g. `source bank-of-anthos.source`) will create environment variables that will simplify the fine tuning of the Dev Trial environment to the Bank of Anthos application. It is recommended that any changes you may have made to the app, or the namespace, be captured in this file and then execute the following command (on a bash command line)

```sh
source bank-of-anthos.source
```

The default cpu and memory parameters and optimization steps that are in the default Dev Trial manifest are appropraite for the Bank of Anthos applicatin, so the only changes that need to be made manually, are the replacement of the four parameters described above.

You can also leverage this helper script to make the required changes (assuming your bank-of-anthos.source file is current):

```sh
update-opsani-manifest.sh
```

## Install the opsani servo via the opsani-manifests.yaml document
  
```sh
kubectl apply -f opsani-manifests.yaml
```

In addition, there are a few additional annotations and labels required, and we will want Opsani's servo to inject the envoy sidecar into the target Deployment under optimization. you can run the inject-sidecar.sh script to enable these modifications, or follow the output of the servo log from the servo deployment.

Once the envoy is injected, you can use the `update-svc.sh` script to redirect the service to the envoy port (9980 by default) 

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

Clean-up is as follows:

```sh
./update-svc.sh ${SERVICE} 8080
./eject-sidecar.sh
kubectl delete -f opsani-manifests.yaml
```
