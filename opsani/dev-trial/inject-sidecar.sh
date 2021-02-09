#!/bin/bash
set -e
source bank-of-anthos.source

echo "Updating deployment adding the envoy sidecar"

if [ -z "$(kubectl -n ${NAMESPACE} get deploy servo)" ]; then
  echo "Servo isn't deployed, perhaps run kubectl apply -f opsani-manifests.yaml first?"
  exit 1
fi

kubectl -n ${NAMESPACE} patch deployment ${DEPLOYMENT} -p '{"spec": {"template": {"metadata": {"annotations": {"prometheus.opsani.com/path": "/stats/prometheus", "prometheus.opsani.com/port": "9901", "prometheus.opsani.com/scheme": "http", "prometheus.opsani.com/scrape": "true"}}}}}'
kubectl -n ${NAMESPACE} patch deployment ${DEPLOYMENT} -p '{"spec": {"template": {"metadata": {"labels": {"sidecar.opsani.com/type": "envoy"}}}}}'
kubectl -n ${NAMESPACE} exec -c servo deploy/servo -- servo --token-file /servo/opsani.token inject-sidecar -n ${NAMESPACE} -s ${SERVICE} deployment/${DEPLOYMENT}
./update-svc.sh envoy
