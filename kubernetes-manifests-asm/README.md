# Kubernetes ASM Manifests

This folder contains an alternate set of Kubernetes Manifests that deploy the Bank of Anthos with ASM support. They should also work with Istio.

Namely - the differences between the Kubernetes Manifests in this directory and those in the [standard Kubernetes Manifests directory](../kubernetes-manifests) is:
* The exposure of the frontend is performed through an Istio Gateway and Virtual Service instead of via a Load Balancer. This is defined in [asm-gateway.yml](asm-gateway.yml).
* Each Pod created by the Deployment for each service is labelled with a `version` label.
* Each service has an accompanying `VirtualService` and `DestinationRule` used for routing traffic.

Before deploying these manifests - you should ensure you have Anthos Service Mesh or Istio installed on your cluster. Additionally you should ensure the namespace you are deploying these manifests to is labelled for automatic sidecar injection:

```
kubectl label namespace <NAMESPACE> istio-injection=enabled --overwrite
```

## Installation

### 1-4 - Follow steps in main README
Follow steps 1 to 4 in [README.md](./README.MD) to setup your Kubernetes Cluster and configure your RSA Keypair

### 5 - Deploy Kubernetes manifests

```
kubectl apply -f ./kubernetes-manifests-asm
```

After 1-2 minutes, you should see that all the pods are running:

```
kubectl get pods
```

*Example output - do not copy*

```
NAME                                  READY   STATUS    RESTARTS   AGE
accounts-db-6f589464bc-6r7b7          2/2     Running   0          99s
balancereader-797bf6d7c5-8xvp6        2/2     Running   0          99s
contacts-769c4fb556-25pg2             2/2     Running   0          98s
frontend-7c96b54f6b-zkdbz             2/2     Running   0          98s
ledger-db-5b78474d4f-p6xcb            2/2     Running   0          98s
ledgerwriter-84bf44b95d-65mqf         2/2     Running   0          97s
loadgenerator-559667b6ff-4zsvb        2/2     Running   0          97s
transactionhistory-5569754896-z94cn   2/2     Running   0          97s
userservice-78dc876bff-pdhtl          2/2     Running   0          96s
```

### 6 - Get the frontend IP

```
kubectl get svc istio-ingressgateway -n istio-system | awk '{print $4}'
```

*Example output - do not copy*

```
EXTERNAL-IP
35.223.69.29
```

### 7 - Follow steps in main README
Follow step 7 in [README.md](./README.MD) to access the Bank of Anthos web frontend