#!/bin/bash

if [ -z "${NAMESPACE}" ]; then
  echo "You must set the NAMESPACE enviornment variable"
  echo "e.g. `export NAMESPACE=bank-of-anthos-opsani`"
  exit 1
fi
echo "create JWT token and store in k8s secret"
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create -n ${NAMESPACE} secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
rm ./jwt*key*

echo "Launch into ${NAMESPACE}"

kubectl apply -n ${NAMESPACE} -f ../kubernetes-manifests/
