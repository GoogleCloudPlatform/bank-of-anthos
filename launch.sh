#!/bin/bash

echo "launching bank of anthos"

NAMESPACE=bank-of-anthos

echo "create a namespace for bank of anthos"
kubectl create namespace ${NAMESPACE}

echo "enable standard Kublet derived metrics-service for HPA"

kubectl apply -f kubernetes-manifests/metrics/

echo "create JWT token and store in k8s secret"
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create -n ${NAMESPACE} secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
rm ./jwt*key*

echo "create OPSANI_TOKEN secret from .env file (from trial directory)"

cat .env | awk -F= '/OPSANI_TOKEN/ {print $2}' > token
kubectl create -n ${NAMESPACE} secret generic servo-token --from-file=./token
rm ./token

echo "Launch into ${NAMESPACE}"

kubectl apply -n ${NAMESPACE} -f kubernetes-manifests/

echo "Launch opsani servo in ${NAMESPACE} namespace"

kubectl apply -n ${NAMESPACE} -f bank-of-anthos-servo.yaml

echo "Launch bank-of-anthos load generator in ${NAMESPACE} namespace"

# nohup kubernetes-manifests-loadgenerator/genload.sh >& loadgen_output.log &
kubectl apply -n ${NAMESPACE} -f kubernetes-manifests-loadgenerator/loadgenerator.yaml

echo "Apply fixes for opsani-servo dev-trial"

# capture deployment before modifications, this should be the same as what is in kubernetes-manifests already
# kubectl -n ${NAMESPACE} get deployment ${DEPLOYMENT} -o yaml > pre-envoy-${DEPLOYMENT}.yaml
kubectl -n ${NAMESPACE} patch deployment frontend -p '{"spec": {"template": {"metadata": {"annotations": {"prometheus.opsani.com/path": "/stats/prometheus", "prometheus.opsani.com/port": "9901", "prometheus.opsani.com/scheme": "http", "prometheus.opsani.com/scrape": "true"}}}}}'
kubectl -n ${NAMESPACE} patch deployment frontend -p '{"spec": {"template": {"metadata": {"labels": {"sidecar.opsani.com/type": "envoy"}}}}}'
kubectl exec -c servo deploy/servo -- servo --token-file /servo/opsani.token inject-sidecar -n ${NAMESPACE} -s frontend deployment/frontend

echo "launch load generator updates locally"
nohup kubernetes-manifests-loadgenerator/genload.sh & tail -f nohup.out