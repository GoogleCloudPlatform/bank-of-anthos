# Deploy Bank of Anthos for Opsani Optimization Trials

Bank of Anthos is a polyglot application that can be used for a number of purposes. Opsani is providing this update to support optimization trials with enough scale and a transaction-defined load generator.

This will support your efforts in deploying and validating this application.

## Prerequisites and Components

1. `kubectl` cli command version appropriate to your cluster
2. bash command line interpreter (to run the deployment scripts)
3. target kubernetes cluster with at least **8** AWS m5.xl equivalent nodes available exclusively for this test
4. ability to create a namespace, or define a namespace in the NAMESPACE environment variable for Bank of Anthos
5. ability to create the metrics-service (or already have it installed) in the kube-systems administrative namespace

## QUICKSTART

Run the `deploy.sh` script which will attempt to validate the pre-requisites, install any missing k8s service components, and install the Bank of Anthos application:

```sh
cd opsani && ./deploy.sh
```

To specify a namespace other than the default, set the NAMESPACE environment variable:

```sh
NAMESPACE=my-ns ./deploy.sh
```

To use envoy sidecars (useful for Prometheus scraping) set the ENVOY_SIDECAR environment variable:

```sh
ENVOY_SIDECAR=true ./deploy.sh
```

## Install Bank of Anthos (Manually)

The following commands will deploy the basic Bank-of-Anthos app, updated to use more realistic resources (requests/limits), and a loadgenerator deployment that should drive 3-5 frontend pods to run and scale up to ~10 pods over time (Currently ~ 1 hour).

The following commands are run by the above `deploy.sh` script, but can be run manually instead:

### Ensure kubectl is installed and pointing to your cluster

The following command will ensure that a) `kubectl` is installed, b) that you can talk to the cluster and c) that you see at least 6 nodes (the output should be a number).

```sh
kubectl get nodes | grep 'internal' | wc -l
```

### Ensure you have a namespace and to simplify followon processes, that the namespace is default

```sh
echo "ensure NAMESPACE is an environment variable":
export NAMESPACE=${NAMESPACE:-bank-of-anthos-opsani}
if [ "`kubectl create ns ${NAMESPACE} >& /dev/null; echo $?`" ]; then
  echo `kubectl get ns ${NAMESPACE} | grep ${NAMESPACE}`
fi
```

Also, you may want to add the namespace to your kubeconfig as the "Default" for this cluster:

```sh
kubectl config set-context `kubectl config get-contexts | awk '/^\*/ {print $2}'` --namespace ${NAMESPACE}
```

### Ensure that the metrics service is installed and running

Metrics are needed to run the HPA pod autoscaler, and are simple point in time cpu and memory data captured from
the kubelet service on each node. You need access to the kube-system namespace and the ability to create Cluster Roles and Cluster Role Bindings in order to apply this manifest from the Kubernetes metrics-sig:

```sh
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Finally, we can install Bank-of-Anthos

Step one is to create a JWT token to support login via the Web UI

```sh
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create -n ${NAMESPACE} secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
rm ./jwt*key*
```

Step two is to launch all of the manifests from the kubernetes-manifests directory which will complete the application deployment.

```sh
kubectl apply -n ${NAMESPACE} -f ../kubernetes-manifests/
```

### Verify that the service is up and running

We can check to ensure that our pods are starting (this may take a moment):

```sh
kubectl -n ${NAMESPACE} get pods -w
```

This will wait and show you pods as they come online.  type ^C (control-C) to quit watching for new pods.

Alternately, we can launch a port-forward to enable access to the Frontend service from our local machine:

```sh
kubectl port-forward -n ${NAMESPACE} svc/frontend 8080:http &
```

You should then be able to point to [http://localhost:8080](http://localhost:8080) and get a login page.  The default user is `testuser` and the default password is `password`.

## Load generation

Load is automatically generated in a dynamic fashion with the loadgenerator pod.  Opsani has modified
this with the latest version of locust.io, and includes a dynamic sinusoidal load pattern.  You can modify the
parameters of the `kubernetes-manifests/loadgenerator.yaml` document with the following parameters:

  STEP_SEC: seconds per step, longer will generate a longer load range, usually 10 is good for initial tests, and 600 for longer term load.
  USER_SCALE:  Number of users to vary, the more the heavier the load.  180 appears to be a good starting point for reasonable load.
  SPAWN_RATE: How quickly to change during the step, there is likely no need to change this parameter.
  MIN_USERS: As the sinusoidal shape varies between "0" and "1" multiplied by the USER_SCALE parameter, it is often good to ensure some load, we set this as 50 by default.

## Starting Optimization

At this point, the Bank of Anthos application should be running on your Kubernetes cluster and should have dynamic load reaching it. You are now ready to install the Opsani servo to begin optimization.

To do so, we suggest that you follow [dev-trial-README](dev-trial/README.md) for the simplest installation procedure. Alternatively, if you would like a more manual approach, the README.md located in the `servo_install.tar.gz` bundle that you downloaded is also suitable. If you do not have `servo_install.tar.gz`, check https://console.opsani.com or contact your Opsani support member.

## Uninstall Bank-of-Anthos

If a namespace was created for this project, the simplest approach is to simply delete the namespace.

Alternatively, clean out the deployed manifests:

```sh
kubectl delete -n ${NAMESPACE} -f ../kubernetes-manifests/
```

We will also want to clean up the manually deployed jwt-key secret:

```sh
kubectl delete secret jwt-key
```

And to really clean things out, you can delete the namespace and the metrics service as well:

```sh
kubectl delete ns ${NAMESPACE}
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
