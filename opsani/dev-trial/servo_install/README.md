```console
  .oooooo.                                              o8o
 d8P'  `Y8b                                             `"'
888      888 oo.ooooo.   .oooo.o  .oooo.   ooo. .oo.   oooo
888      888  888' `88b d88(  "8 `P  )88b  `888P"Y88b  `888
888      888  888   888 `"Y88b.   .oP"888   888   888   888
`88b    d88'  888   888 o.  )88b d8(  888   888   888   888
 `Y8bood8P'   888bod8P' 8""888P' `Y888""8o o888o o888o o888o
              888
             o888o
Dev // Cloud Native Optimization for Kubernetes applications
```

Opsani is your optimization copilot. Opsani will show you how to reduce your
infrastructure spending and amplify your application performance. This resource
will guide you through connecting your application to an Opsani Optimizer
backend and getting started with cloud native workload optimization on
Kubernetes.

Opsani optimizes your application by performing experiments that apply
configurations to your environment and evaluating the impact that they have on
cost and performance.

Experiments are run by creating a tuning Pod, based off of a Kubernetes
Deployment object of your choice, joining it to the Kubernetes Service that is
distributing traffic to the Pods in your Deployment, and evaluating its cost and
performance against its sibling Pods.

Optimization is orchestrated by a single Pod called the Servo, which handles all
interaction between your application and the Opsani Optimizer. Metrics data such
as replica counts, resource sizing, latencies, and request throughput are
gathered by the Servo to inform the Optimizer. Data is always handled in the
aggregate and is only used to drive optimization of your app.

Sound good? Let's ride.

## Prerequisites

Before we roll up our sleeves, let's make sure that we have all the pieces on
the board. Completing this guide requires the following:

1. A [Kubernetes](https://kubernetes.io/) cluster running v1.16.0 or higher.
2. Local access to
   [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) for
   applying manifests to the cluster.
3. Access rights to list, create, read, update, and delete Deployments, Pods,
   Config Maps, Services, and Service Accounts through an in-cluster Service
   Account or a configured
   [kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
   file.
4. An application to be optimized, running as a
   [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
   in the Kubernetes cluster.
5. An understanding of how ingress traffic is directed into a Kubernetes
   [Service](https://kubernetes.io/docs/concepts/services-networking/service/)
   and flows into the target Deployment through a TCP port and the ability to
   make changes to the port.
6. Representative traffic flowing to the Deployment through a Kubernetes
   [Service](https://kubernetes.io/docs/concepts/services-networking/service/)
   (e.g., Load Balancer, ClusterIP) from a live source or synthetic load
   generator.

This document provides numerous command examples for reference. For clarity and
brevity, it is assumed that `kubectl` is configured to interact with the target
namespace. In order to copy and paste reference commands without modification,
it is recommended that the active kubeconfig context is set to the target
cluster and has been updated to interact with the target namespace by default.
See [Setting Namespace Context](#setting-kubectl-context-namespace) for details.

All the bases covered? Cool, let's get down to business.

## Deploying the Servo

Before optimization can be started, there are a few things that need to be done.
First off, we need to get the Servo up and running.

1. Update the `opsani-manifests.yaml` file accompanying this document to reflect
   your environment. The following variables must be replaced:
    * `` - Namespace in which the target Deployment is running
      (e.g., `apps`).
    * `` - Name of the target Deployment to optimize (e.g.,
      `webapp`).
    * `` - Name of the container targeted for optimization (e.g.,
      `main`). Must be the name of a container in the Pod spec of the target
      Deployment. When omitted, the first container in the Pod is targeted.
      Container names can be displayed via:

      ```console
      kubectl get deployments -o \
        jsonpath="{.spec.template.spec.containers[*].name}" \
        [DEPLOYMENT]
      ```

    * `` - Service supplying traffic to the target Deployment
      (e.g., `webapp-service`).

      Note that if your Service exposes more than one port, you will need to add
      a `port` argument to the servo configuration identifying the port by
      *name* or *number* in order to disambiguate the target port. For example:
      `port: 8080` or `port: http`.

2. Configure the resource ranges for the CPU and memory configurations that you
   would like the optimizer to explore. Within the `opsani-manifests.yaml` file
   in the `ConfigMap` in which you have just configured the namespace,
   deployment, etc. there are `cpu` and `memory` keys that define the range of
   values to explore during optimization.

   Resource values are configured using the same resource units supported by
   Kubernetes as as detailed in the [Resource Units in
   Kubernetes](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#resource-units-in-kubernetes)
   documentation.

   CPU values are expressed in millicores (i.e. `1000m`) or integer/floating
   point values corresponding to full core units (i.e. `1` or `2.0`). Values are
   interchangeable and can be mixed within range declarations -- `1 == 1.0 ==
   1000m`.

   Memory values are expressed in bytes when specified as integers but are
   typically configured using SI power-of-two byte values (e.g., `128 MiB`).
   These units are interchangeable and can be mixed within range declarations --
   `128974848 == 129e6 == 129M == 123Mi`.

   The minimum end of the range should be no lower than the minimum amount of
   CPU and memory that you know to be workable to run your application. If set
   below a workable value, the optimizer will waste cycles exploring unworkable
   and wait for health checks to fail or metrics to report unacceptable error
   rates (depending on your failure modes).

   The maximum should be configured to
   the upper bounds of resources you are willing to allocate to the container
   (up to and including the maximum resourcing schedulable on the nodes in the
   cluster). The maximum value can be set well above your expected resource
   allocations. The optimizer will determine if there are diminishing returns
   and discard inefficient configurations. The only caveat with maximum
   resourcing is to avoid configuring a top end range that cannot actually be
   scheduled on the available nodes, else the optimizer will waste cycles
   attempting to explore configurations that Kubernetes will refuse to schedule.

   The `step` setting defines the base value that new configurations will be a
   multiple of. For example, given a memory step size of `32 MiB` and a current
   memory allocation of `128 MiB` for the container, the optimizer might
   prescribe new values of `160 MiB` (128 + 32), `64 MiB` (128 - (32 \* 2)), or
   `256 MiB` (128 + (32 \* 4)) but would never prescribe `144 MiB` (128 + 16).
   The preconfigured step values are acceptable for most applications.

3. Apply the Servo manifests:

    ```console
    kubectl apply -f opsani-manifests.yaml && \
      kubectl wait --for=condition=available --timeout=5m deployment/servo
    ```

4. Once the Servo becomes available, it will execute a set of health checks to
   verify readiness to run. The Servo logs will provide feedback about status of
   the checks and helpful hints for addressing any problems. When the Deployment
   is found healthy, the logs will report that the Servo is ready and
   optimization will begin.

    ```console
    kubectl logs -f -c servo --pod-running-timeout=10m \
      -l app.kubernetes.io/name=servo
    ```

    If the logs command times out, move to [Debugging Servo Deployment](#debugging-servo-deployment).

## Instrumenting your application

In order to begin optimization, the Servo must be connected to the application
under optimization. There are a couple of tasks to be completed.

As a given Kubernetes cluster can have an arbitrary
number of applications and services running, some metadata needs to be applied
so that the Servo can observe and orchestrate the application you want to
optimize. A set of annotations and labels need to be applied to facilitate
discovery within the cluster.

Next, optimization requires access to metrics that are used to evaluate the
effects of configuration changes applied to the application during optimization.
To make optimization as easy as possible, the Servo handles metrics collection
and aggregation. In order to generate the necessary metrics, an
[Envoy](https://www.envoyproxy.io/) sidecar is injected into the `PodTemplate`
specification of the `Deployment` for the application under optimization. After
the Envoy sidecars are injected and deployed, the `Service` supplying ingress
traffic to `Pod` instances of the `Deployment` is updated to pass traffic
through the proxy before being processed by the primary application container.
Envoy then emits the metrics required for optimization, they are aggregated by
the Servo, and reported to the Optimizer for analysis.

The steps for making these changes are detailed below but are also reported into
the Servo logs when a particular aspect of the configuration fails a health
check. It is strongly advised that you tail the Servo logs and pay attention to
the feedback it provides during deployment. The **Hint** output provides copy
and pasteable commands that support an iterative, interactive install flow. You
can follow the logs by running:

```console
kubectl logs -f -c servo --pod-running-timeout=10m \
  -l app.kubernetes.io/name=servo
```

### Automatic configuration

The Servo supports the notion of **remedies** which enable the automatic
remediation of known issues. If you wish to enable remedies, run the following command:

```console
kubectl patch deployment servo --type=json \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--remedy"}]'
```

Once the patch is applied, the Servo Pod will be redeployed and you will need to
follow the logs again when the new Pod is up.

### Manual configuration

The steps required for completing the configuration are as follows:

1. Apply the required annotations (requires `[DEPLOYMENT]` arg):

    ```console
    kubectl patch deployment [DEPLOYMENT] \
      -p '{"spec": {"template": {"metadata": {"annotations": {"prometheus.opsani.com/port": "9901", "prometheus.opsani.com/scheme": "http", "prometheus.opsani.com/path": "/stats/prometheus", "prometheus.opsani.com/scrape": "true"}}}}}'
    ```

2. Apply the required labels to the `PodTemplate` of the `Deployment` (requires
   `[DEPLOYMENT]` arg):

    ```console
    kubectl patch deployment [DEPLOYMENT] \
      -p '{"spec": {"template": {"metadata": {"labels": {"sidecar.opsani.com/type": "envoy"}}}}}'
    ```

3. Inject the Envoy sidecar into the `PodTemplate` of the `Deployment` (requires
   `[NAMESPACE]`, `[DEPLOYMENT]`, and `[SERVICE]` args):

    ```console
    kubectl exec -c servo deploy/servo \
      -- servo --token-file /servo/opsani.token \
      inject-sidecar -n [NAMESPACE] -s [SERVICE] deployment/[DEPLOYMENT]
    ```

4. Update the `Service` supplying traffic to the `Deployment` so that Envoy will
   begin emitting metrics (requires `[SERVICE]` and `[PORT]` args and note that
   the `Service` type is assumed to be `LoadBalancer`):

    ```console
    kubectl patch service [SERVICE] \
      -p '{"spec": {"type": "LoadBalancer", "ports": [{"protocol": "TCP", "port": [PORT], "targetPort": 9980}]}}'
    ```

Once all checks are passing, the servo will enter its standard run mode and
begin interacting with the Opsani API and the Optimizer. A tuning Pod will be
created and data points will begin reporting into the Opsani Console. Opsani
launches in measure-only mode which refrains from making changes to your
infrastructure until you are ready.

## Next Steps

Once the installation is completed, optimization can be configured to match your
specific goals.

## Troubleshooting

If you run into issues completing setup, there are a number of tools at your
disposal for triaging and resolving issues.

### Debugging Servo Deployment

If errors are encountered during servo deployment, there are a few things to
evaluate:

1. Is there a servo pod?

    ```console
    kubectl get pod -l app.kubernetes.io/name=servo
    ```

  If no servo pod is identified, then the deployment was not successful or the
  wrong namespace has been targeted. Retrace your steps and verify that all
  assumptions such as the namespace are correct.

1. Has there been a scheduling error?

  When a servo Pod is created but remains in the `pending` status, it often
  indicates a scheduling error due to a lack of available resources on the
  cluster. Describing the Pod and looking at the event status is essential to
  understanding the error and how to resolve it.

  ```console
  kubectl describe pod -l app.kubernetes.io/name=servo
   ```

1. Are both containers healthy?

  Once the sidecar is deployed, all Pods that are part of the target Deployment
  will begin reporting on 2 containers. Ensure that each of these containers is
  reporting as ready.

1. Is the servo connecting to the API?

  Check that servo is connecting to the Opsani API by reviewing the servo logs.
  Connectivity errors will be reported into the logs and will trigger
  exponential backoff and retry behaviors.

  The HTTP status code of the error report is indicative of the problem. A `404
  (Not found)` error indicates a problem in the optimizer configuration (e.g.,an
  invalid `OPSANI_OPTIMIZER`, a bad base URL, or an outbound firewall/proxy).

  A `401 (Unauthorized)` status code indicates that an incorrect API token has
  been provided and could not be verified.

  Any 5xx error would indicate an upstream failure in the runtime system or
  infrastructure hosting the Opsani platform.

### Running Servo checks

The Servo exposes a rich set of preflight checks that verify the correctness of
the configuration. These checks are run automatically during normal operation
startup. When troubleshooting specific issues, it can be helpful to run one or
more of these checks directly. This can be done via the `kubectl exec` (when a
running Servo Pod is available):

```console
kubectl exec -c servo deploy/servo \
  -- servo --token-file /servo/opsani.token check
```

or via `kubectl run` (as an adhoc task)

```console
kubectl run servo --image=opsani/servox:edge --command \
  -- servo -c /servo/servo.yaml --token-file \
  /servo/opsani.token check --wait=10s
```

### Tailing Servo logs

The Servo provides extensive logging output that is invaluable in debugging.
Logs can be tailed by executing:

```console
kubectl logs -f -c servo -l app.kubernetes.io/name=servo
```

### Debugging traffic metrics

Optimization requires data about the performance of the service under
optimization. Opsani Dev relies on Envoy proxy sidecar containers that receive
traffic from a Kubernetes service and proxies it back to the service under
optimization. If throughput or latency metrics are flatlined, it can either
point to an issue with metrics generation (at the Envoy level) or metrics
aggregation (at the Prometheus level).

A good way to differentiate between the two possible root causes is to tail the
Envoy proxy logs. If HTTP requests are being logged, then they are being
instrumented and exposed as scrapeable metrics and the issue is at the
Prometheus aggregation level. If requests are not being logged but are
succeeding, then the issue is related to sidecar proxy configuration -- traffic
is not being intercepted by the proxy. If requests are failing, then the proxy
configuration is misaligned and ingress traffic from the Kubernetes service is
being misrouted. This can either be caused by the proxy is not listening on the
port that the service is sending traffic to, in which case Envoy will show
nothing in the logs, or by the Envoy proxy passing traffic back to the wrong
port on the service under optimization, in which case the Envoy logs will show
inbound requests with a 4xx/5xx status code from the upstream service.

The key to debugging these cases is to examine the Envoy proxy logs and analyze
what you see as described.

To tail these logs, run:

```console
kubectl logs -f -c opsani-envoy -l sidecar.opsani.com/type=envoy
```

#### Why am I not receiving traffic after an adjustment?

When the Servo applies an adjustment to the tuning instance, it destroyed and
recreated. In certain circumstances such as when utilizing synthetic traffic
delivered via a load generator, the clients may develop an affinity to the main
instances while the tuning instance is being adjusted. This is the result of
HTTP persistent connections where the client utilizes long-lived TCP connections
to the Kubernetes Service to avoid the overhead of setting up a new TCP
connection and completing a TLS handshake. The problem is that when the
persistent connections are not severed, the tuning instance is starved of
traffic and will rightfully begin reporting flatlined metrics because all of the
requests are being handled by the main instances.

To handle this, a sophisticated load generator such as [k6](https://k6.io/) can
be utilized that supports precise control over the TCP connections or the load
generator can be put on a scheduled restart to sever the connections
periodically.

### Port-forwarding to Prometheus

The Servo runs with a Prometheus sidecar container. If metrics are not available
for whatever reason, it can be helpful to directly connect to Prometheus in
order to inspect the targets and run adhoc queries. To do so:

```console
kubectl port-forward deployment/servo 9090:9090
```

Then open [http://localhost:9090](http://localhost:9090) in your browser.

### Elevating log levels

The Servo emits extensive logging during operation. The default log level of
`INFO` is designed to provide consistent feedback that is easy to follow in real
time without becoming overwhelming. When troubleshooting an issue, it may become
desirable to run the Servo at a logging level of `DEBUG` or `TRACE`. To do so:

```console
kubectl set env deployment/servo SERVO_LOG_LEVEL=DEBUG
kubectl rollout restart deployment/servo
```

### Restarting the Servo

The Servo is built with extensive health checks, timeouts, and an asynchronous
architecture that will deliver consistent feedback during normal operations. But
things can go wrong and when they do sometimes a hard restart is the path of
least resistance. To do so:

```console
kubectl rollout restart deployment/servo
```

## Getting Help

The Opsani support team is standing by to assist you with any issues encountered
during deployment. Send an email to
[support@opsani.com](mailto:support@opsani.com) and we will lend you a hand.

## Appendices

### Setting kubectl context namespace

```console
kubectl config set-context --current --namespace=[NAMESPACE]
```

### Optimizing with synthetic load

If you see metrics fall to zero during optimization following an adjustment,
then you may have an issue with persistent connections.

When utilizing a load generator to deliver synthetic load to an application
under optimization by Opsani Dev, care must be taken with regard to persistent
connections.

Most load generators utilize HTTP and TCP persistent connections to pipeline
requests and avoid the overhead of establishing TCP connections and completing
SSL handshakes for performance reasons.

This can become problematic during optimization because as the tuning pod is
reconfigured and enters/exits the pool of available pods to receive traffic from
the upstream Kubernetes service it can become starved of traffic because the
persistent connections are bind the load generator against the remaining pods in
the service.

The solution is to snap the persistent connections periodically which sadly is a
capability that is not supported by many widely deployed load generators. Opsani
recommends [k6](https://k6.io/) and can provide reference scripts for managing
persistent connections during a k6 load generation cycle or more crude solutions
such as restarting the load generation on a fixed time interval can deliver a
similar effect.


### Using an alternate API base URL

```console
kubectl set env deployment/servo OPSANI_BASE_URL=https://custom-api.opsani.com
kubectl rollout restart deployment/servo
```

### Building Docker images

If you are unable to pull Docker images from the [Opsani Docker
Hub](https://hub.docker.com/r/opsani/servox) or would prefer to build the images
yourself, instructions are available in the [ServoX
README](https://github.com/opsani/servox#docker--compose).

### Handling HTTPS Container Ports

The Opsani Envoy sidecar supports proxying container ports that carry HTTPS
traffic with some additional configuration. Because Opsani requires knowledge of
request/response details such as request counts, latencies, and response status
codes, the proxy must decrypt and reencrypt traffic as it passes through the
proxy so that these details are accessible (otherwise we are blindly proxying
opaque TCP streams).

Proxying HTTPS container ports requires the following artifacts:

1. The certificate chain for the HTTPS service (referred to as
   `certificate_chain.pem`).
2. The private key for decrypting traffic (referred to as `private_key.pem`).

Enabling encrypting proxying is done by making the following modifications to
the `opsani-envoy` container:

1. Mounting `private_key.pem` and `certificate_chain.pem` to `/etc/` in the
   container filesystem (e.g., via Kubernetes Secrets).
2. Setting the `OPSANI_ENVOY_PROXIED_CONTAINER_TLS_ENABLED` environment variable
   to `true` on your application deployment (or `opsani-envoy` container):

  ```console
  kubectl set env deployment/[app-name] OPSANI_ENVOY_PROXIED_CONTAINER_TLS_ENABLED=true
  ```

### Optimizing across namespaces

In some instances, it can be useful to run the Servo in a different namespace
than the target app. Doing so requires extending the `ClusterRoleBinding`
manifests to include subjects for the `servo` Service Account in both the
namespaces running the Servo and the application under optimization.

For example, if the target application is running in the namespace `webapps` and
the Servo is deployed to the namespace `opsani`, the `ClusterRoleBinding`
manifest would need to look like:

```yaml
# Bind the Servo Cluster Role to the servo Service Account
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: servo
  labels:
    app.kubernetes.io/name: servo
    app.kubernetes.io/component: core
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: servo
subjects:
- kind: ServiceAccount
  name: servo
  namespace: webapps
- kind: ServiceAccount
  name: servo
  namespace: opsani

---
# Bind the Prometheus Cluster Role to the servo Service Account
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
  labels:
    app.kubernetes.io/name: prometheus
    app.kubernetes.io/component: metrics
    app.kubernetes.io/part-of: servo
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: servo
  namespace: webapps
- kind: ServiceAccount
  name: servo
  namespace: opsani
```
