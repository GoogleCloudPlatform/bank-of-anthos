# Troubleshooting Bank of Anthos 

This doc describes how to debug a running instance of Bank of Anthos on a GKE cluster. 

## Background 

The conatiner images used in [`kubernetes-manifests/`](/kubernetes-manifests) correspond to a tagged, stable release (`v0.x.x`) that is ready for public consumption. Per the [README deploy instructions](/README.md), we highly recommend using these stable image tags, not the `latest` tag. The `latest` tag corresponds to latest commit to the main branch and may be less stable. 

No matter what image tags you're using, you may encounter errors when running the Bank of Anthos app. Use the following steps to debug and fix problems. 

## Steps to Debug

- **Make sure the pods are running**. Make sure you have `kubectl` access to your cluster, then run `kubectl get pods`. When the app is healthy, you should see 9 pods: 

```
NAME                                 READY   STATUS    RESTARTS   AGE
accounts-db-0                        1/1     Running   0          14m
balancereader-d887fdb78-gdrsd        1/1     Running   1          15m
contacts-7d559f5444-5j7nj            1/1     Running   0          15m
frontend-78f948f946-qc6m9            1/1     Running   0          15m
ledger-db-0                          1/1     Running   0          14m
ledgerwriter-7d667cf86f-tvssn        1/1     Running   1          15m
loadgenerator-777bd57f48-6642p       1/1     Running   0          15m
transactionhistory-dd999969f-dgjth   1/1     Running   0          15m
userservice-5765f7bf44-7rs2r         1/1     Running   0          15m
```

One or two `RESTARTS` in the pods is expected, as the services sometimes start up before `skaffold` can deploy necessary dependencies (eg. `jwt-secret` mount). You're looking for `STATUS: Running` and `READY: 1/1`. If your cluster's namespace has Istio or Anthos Service Mesh, you would see `READY: 2/2`, since each pod would have a sidecar proxy container.  

- **Make sure all the Kubernetes services are present**. Run `kubectl get service`. You should see a service per pod, except for the loadgen (8 services total). The `frontend` service should have an `EXTERNAL_IP`. Try to reach that `EXTERNAL_IP` in a web browser, or using `curl`. You should see the Bank of Anthos login screen. 

```
accounts-db          ClusterIP      10.48.23.153   <none>          5432/TCP       23d
balancereader        ClusterIP      10.48.26.169   <none>          8080/TCP       23d
contacts             ClusterIP      10.48.29.96    <none>          8080/TCP       23d
frontend             LoadBalancer   10.48.19.116   35.xxx.xx.xxx   80:31279/TCP   23d
ledger-db            ClusterIP      10.48.23.102   <none>          5432/TCP       23d
ledgerwriter         ClusterIP      10.48.28.89    <none>          8080/TCP       23d
transactionhistory   ClusterIP      10.48.20.206   <none>          8080/TCP       23d
userservice          ClusterIP      10.48.19.11    <none>          8080/TCP       23d
```

- The next step to verify your issue is to **clean deploy** the Bank of Anthos app to your cluster:

```
kubectl delete -f kubernetes-manifests
kubectl apply -f kubernetes-manifests
```

If your problem persists, proceed to the Common Problems section below.

## Common Problems 

### Pod has `STATUS: CrashLoopBackOff` 

If a pod is crash-looping, this means the process inside the container has exited with an error. Run `kubectl logs <pod-name>` to get the container logs. It is likely that a Java or Python exception caused the service to crash. [**File a Github issue**](https://github.com/googlecloudplatform/bank-of-anthos/issues) if this is happening, as it could correspond to a widespread outage (or an environment problem that could affect other users). When filing your issue, include the crash logs for the failing pods. 


### Pod is stuck in `STATUS: Pending` or `READY: 0/1` 

Run `kubectl describe pod <pod-name>` to get details about the state of the Pod. At the bottom of the output, you should see a set of events: 

```
Events:
  Type     Reason       Age                From                                             Message
  ----     ------       ----               ----                                             -------
  Normal   Scheduled    73s                default-scheduler                                Successfully assigned default/balancereader-fb6784fc-9fw2k to gke-toggles-default-pool-28882412-xljt
  Warning  FailedMount  72s (x2 over 72s)  kubelet, gke-toggles-default-pool-28882412-xljt  MountVolume.SetUp failed for volume "publickey" : secret "jwt-key" not found
  Normal   Pulling      70s                kubelet, gke-toggles-default-pool-28882412-xljt  Pulling image "gcr.io/my-cool-project/bank-of-anthos/gcr.io/bank-of-anthos-ci/balancereader:ver.0-171-gd459ddb-dirty@sha256:5b178bd029d04e25bf68df57096b961a28dfb243717d380524a89de994d81ff6"
  Normal   Pulled       69s                kubelet, gke-toggles-default-pool-28882412-xljt  Successfully pulled image "gcr.io/my-cool-projectt/bank-of-anthos/gcr.io/bank-of-anthos-ci/balancereader:ver.0-171-gd459ddb-dirty@sha256:5b178bd029d04e25bf68df57096b961a28dfb243717d380524a89de994d81ff6"
  Normal   Created      69s                kubelet, gke-toggles-default-pool-28882412-xljt  Created container balancereader
  Normal   Started      69s                kubelet, gke-toggles-default-pool-28882412-xljt  Started container balancereader
  Warning  Unhealthy    4s (x2 over 9s)    kubelet, gke-toggles-default-pool-28882412-xljt  Readiness probe failed: Get http://10.0.1.141:8080/ready: dial tcp 10.0.1.141:8080: connect: connection refused
```

In this case, see the `FailedMount` error that has occured twice `(x2)`. This means that the `jwt-key` -- the JWT public key necessary for the balancereader to authenticate requests -- is not present in the cluster. `skaffold` should automatically deploy this secret - if you have manually deployed the app, follow the README instructions to add the `jwt-key` Secret to your cluster.


Another common problem that you may see in the `Events` is `Insufficient Memory`: 

```
Events:
  Type     Reason            Age                From               Message
  ----     ------            ----               ----               -------
  Warning  FailedScheduling  12s (x3 over 13s)  default-scheduler  0/1 nodes are available: 1 Insufficient memory.
```

This means that your cluster's [Node Pools](https://cloud.google.com/kubernetes-engine/docs/concepts/node-pools) do not have enough capacity to host all the Bank of Anthos workloads, and you either need to use a different cluster, or increase your existing cluster's capacity (see the [GKE docs](https://cloud.google.com/kubernetes-engine/docs/how-to/resizing-a-cluster)). 

### `503` error in the frontend 

You may see a `503: Service Unavailble` error if you have added Istio or Anthos Service Mesh to the cluster namespace where Bank of Anthos is deployed. A 503 error typically comes from an Envoy proxy - either the IngressGateway proxy, or the sidecar proxy for a service pod. For the frontend specifically, the 503 is likely coming from the IngressGateway. 

Make sure you've deployed the `VirtualService` and `Gateway` resources provided in [`istio-manifests/`](/istio-manifests), and that they're deployed into the namespace where the app is running. If you've modified the frontend's Service or Deployment port, make sure the `VirtualService` port is updated, too.  

See the [Istio troubleshooting docs](https://istio.io/latest/docs/ops/common-problems/network-issues/) for more support.


### `404` error in the frontend 

You may see a `404: Not Found` error if you've added a Kubernetes Ingress resource pointing to the `frontend` service, but have misconfigured that resource. Note that for GKE Ingress to work, the service must be of type `NodePort`. By default in `kubernetes-manifests`, the frontend service is of type `LoadBalancer`, so you'd have to change the service type. See the [GKE docs](https://cloud.google.com/kubernetes-engine/docs/tutorials/http-balancer) for more info.  



