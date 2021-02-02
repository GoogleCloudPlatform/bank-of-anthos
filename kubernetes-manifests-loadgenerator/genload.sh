#!/bin/bash

kubectl apply -f kubernetes-manifests-svc-updates/frontend-envoy-svc.yaml
while [ true ]; do
    for item in 0 1 2 3 2 1 2 1 3 1 2 3 2 1; do
	echo "generating load ${item}"
        kubectl apply -f kubernetes-manifests-loadgenerator/loadgenerator-${item}.yaml
        sleep 3600
    done
done
