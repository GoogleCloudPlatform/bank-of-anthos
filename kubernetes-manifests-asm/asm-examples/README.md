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

Here - instead of implementing a delay, we're using the Fault Injection capability to return a HTTP 500 Internal Server Error HTTP response to 50% of the requests.

If you browse to the Bank of Anthos UI at `http://<YOUR INGRESS IP>/` and refresh the page a couple of times. You should notice that approximately 50% of the requests return a `500 Internal Server Error`.

Clean up the changes by re-applying the original manifest:
```
kubectl apply -f ../asm-gateway.yml
```