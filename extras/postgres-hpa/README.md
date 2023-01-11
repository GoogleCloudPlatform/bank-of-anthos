# PostgreSQL with HPA

This directory contains instructions and Kubernetes manifests for overriding the default in-cluster PostgreSQL databases (accountsdb + ledgerdb) with PostgreSQL HA and demonstrate usage of Kubernetes Horizontal Pod Autoscaling with it.

## Files structure

* Directory `helm-postgres-ha` contains configuration of PostgreSQL HA helm chart and source code of PGpool operator
* Directory `hpa` contains manifest files of HPA objects
* Directory `kubernetes-manifests` contains manifest files of Bank of Anthos application with modifications of `resources` section.
* File `loadgenerator.yaml` contains kubernetes objects to run load generation. (should be modified before apply)

> NOTE: This setup was tested with GKE Autopilot which handle provisioning of additional worker nodes.

## Configure HPA

### Prepare HPA for Frontend service

Discover an exact name of frontend’s ingress LoadBalancer using the following command:

```bash
FW_RULE=$(kubectl get ingress frontend -o=jsonpath='{.metadata.annotations.ingress\.kubernetes\.io/forwarding-rule}')
echo $FW_RULE
sed -i "s/FORWARDING_RULE_NAME/$FW_RULE/g" "hpa/frontend.yaml"
```

### Deploy HPA

```bash
kubectl apply -f hpa
```

## Deploy loadgenerator

Wait when application will be available on IP address of load balancer and start this process.

```bash
LB_IP=$(kubectl get ingress frontend -o=jsonpath='{ .status.loadBalancer.ingress[0].ip}')
echo $LB_IP
sed -i "s/FRONTEND_IP_ADDRESS/$LB_IP/g" "loadgenerator.yaml"
```

Apply kubernetes deployment manifest

```bash
kubectl apply -f loadgenerator.yaml
kubectl port-forward "svc/loadgenerator" 8080
```

The load generator has auto-start enabled by default. You should be able to observe it's execution on <http://localhost:8080>
