# Bank of Anthos - Anthos Service Mesh Examples

This directory contains a range of manifests that enable you to explore the functionality of Anthos Service Mesh with the Bank of Anthos.

Before performing any of the steps documented below - you should perform the standard deployment using the [provided ASM Manifests](../).

### 1 - Fault Injection
First - we will experiment with the [Fault Injection capability](https://istio.io/latest/docs/tasks/traffic-management/fault-injection/) of Anthos Service Mesh and inject some faults into the [frontend](../../src/frontend) service.

Inspect the contents of the [frontend-delay-fault-injection.yml](frontend-delay-fault-injection.yml) file. You'll notice the following block under the `route:` section:
```
fault:
    delay:
    fixedDelay: 10s
    percentage:
        value: 50
```

Here we're using the Fault Injection capability to implement a 10 second delay to 50% of the requests that make it to the [frontend](../../src/frontend) service. Apply the manifest with:

```
kubectl apply -f frontend-delay-fault-injection.yml
```

If you browse to the Bank of Anthos UI at `http://<YOUR INGRESS IP>/` and refresh the page a couple of times. You should notice that approximately 50% of the requests are delayed by 10 seconds.

We're not limited to implementing delays - we can also inject other faults such as HTTP Status Codes. Inspect the contents of the [frontend-http500-fault-injection.yml](frontend-http500-fault-injection.yml) file. You'll notice the following block under the `route:` section:
```
fault:
    abort:
    httpStatus: 500
    percentage:
        value: 50
```

Here - instead of implementing a delay, we're using the Fault Injection capability to return a `HTTP 500 Internal Server Error` HTTP response to 50% of the requests.

If you browse to the Bank of Anthos UI at `http://<YOUR INGRESS IP>/` and refresh the page a couple of times. You should notice that approximately 50% of the requests return a `500 Internal Server Error` response.

Clean up the changes by re-applying the original manifest:
```
kubectl apply -f ../asm-gateway.yml
```

### 2 - Traffic Shifting
Next - we will experiment with the [Traffic Shifting capability](https://istio.io/latest/docs/tasks/traffic-management/traffic-shifting/) of Anthos Service Mesh by deploying a new version of our [frontend](../../src/frontend) service and managing traffic between the new version and the original.

The frontend service is configured to look for an environment variable named `BANK_NAME`. This environment variable is then shown in the navigation bar of the frontend service. Instead of building a new version of the container, for simplicity we'll instead create a new deployment with a different `BANK_NAME` variable set. This will easily enable us to determine which version of the frontend we are hitting.

Inspect the contents of the [frontend-custom-deployment.yml](frontend-custom-deployment.yml) file. You'll notice that the deployment is similar to the original deployment, but with some minor changes:
1. We've changed the `name:` of the deployment to `frontend-custom`
2. We've changed the `version:` label and `VERSION` environment variable to `v0.2.0-custom`
3. We've added a new environment variable named `BANK_NAME` and set the value to `Bank of Custom`

When applied - this manifest will create a new deployment named `frontend-custom` with the same container image as the `frontend` service - but with the changes detailed above. It will also update the `frontend-destination` Destination Rule with a new subset that will enable us to send traffic to a specific version.

Apply the manifest:

```
kubectl apply -f frontend-custom-deployment.yml
```

Check that the new deployment was successfully created:
```
kubectl get deployments
```

*Example output - do not copy*

```
NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
frontend-custom      1/1     1            1           67m
```

At this point - we've successfully deployed the new version of the frontend application - but we're not sending any traffic to it. Inspect the contents of the [frontend-custom-50-50.yml](frontend-custom-50-50.yml) file. You'll notice that we now have two destinations configured under the route:

```
- destination:
    host: frontend
    subset: v0-2-0
    weight: 50
- destination:
    host: frontend
    subset: v0-2-0-custom
    weight: 50
```

Here, we're configuring Anthos Service Mesh to evenly distribute the traffic between the original version of the application, and our new `v0.2.0-custom` version. Apply the manifest:

```
kubectl apply -f frontend-custom-50-50.yml
```

If you browse to the Bank of Anthos UI at `http://<YOUR INGRESS IP>/` and refresh the page a couple of times. You should notice that the bank name in the navigation bar changes between `Bank of Anthos` and `Bank of Custom`. This happens as Anthos Service Mesh directs us between different versions of our application.

You can experiment by editing the [frontend-custom-50-50.yml](frontend-custom-50-50.yml) file and changing the traffic distributions. You can also switch over traffic completely to our `v2.0.0-custom` version by applying the [frontend-custom-100-0.yml](frontend-custom-100-0.yml) manifest.

Clean up the changes by deleting the deployment and re-applying the original manifest:
```
kubectl delete deployment frontend-custom
kubectl apply -f ../asm-gateway.yml
```