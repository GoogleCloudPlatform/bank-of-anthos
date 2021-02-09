#!/bin/bash

if [ -z "${NAMESPACE}" ]; then
  if [ ! -z "`kubectl get ns bank-of-anthos-opsani`" ]; then
   NAMESPACE=bank-of-anthos-opsani
   echo "Setting Kubernetes namespace to 'bank-of-anthos-opsani'"
   echo "You will need to ensure that your opsani services use"
   echo "this same namespace parameter"
  else
   echo "You must set the NAMESPACE enviornment variable"
   echo "e.g. `export NAMESPACE=bank-of-anthos-opsani`"
   exit 1
  fi
fi
echo ""
echo "create JWT token and store in k8s secret for Bank-of-Anthos"
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create -n ${NAMESPACE} secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
rm ./jwt*key*

echo "Launch Bank-of-Anthos into ${NAMESPACE}"

kubectl apply -n ${NAMESPACE} -f ../kubernetes-manifests/
