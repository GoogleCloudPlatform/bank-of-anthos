#!/bin/bash

DEPLOYMENT=frontend

echo "Removing servo and servo secrets"

kubectl delete -f bank-of-anthos-servo.yaml
kubectl delete secret servo-token

echo "Resetting the deployment to default"

kubectl apply -f kubernetes-manifests/${DEPLOYMENT}.yaml

# echo "Remove metrics service"
# kubectl delete -f kubernetes-manifests/frontend-hpa.yaml
# kubectl delete -f kubernetes-manifests/userservice-hpa.yaml
# kubectl delete -f kubernetes-manifests/metrics/
