#!/bin/bash
source bank-of-anthos.source

echo "Updating deployment removing the envoy sidecar"
./update-svc.sh app
kubectl -n ${NAMESPACE} exec -c servo deploy/servo -- servo --token-file /servo/opsani.token eject-sidecar -n ${NAMESPACE} deployment/${DEPLOYMENT}
