#!/bin/bash

echo "Removing the bank-of-anthos"
kubectl delete -f ../kubernetes-manifests
kubectl delete -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl delete ns ${NAMESPACE:-bank-of-anthos-opsani}
