#!/bin/bash

gcloud config set project $PROJECT_ID

# Create static IP
gcloud compute addresses create boa-single-cluster-ip --global

# Store the value of the static IP as a variable
IP=`gcloud compute addresses describe boa-single-cluster-ip --global --format="value(address)"`

# Create cert
openssl genrsa -out private.key 2048

openssl req -new -key private.key -out frontend.csr \
    -subj "/CN=${IP}"

openssl x509 -req -days 365 -in frontend.csr -signkey private.key \
    -out public.crt

# Create secret from cert
kubectl create secret tls frontend-tls --cert=public.crt --key=private.key

# Deploy app
kubectl apply -f ../../extras/jwt/jwt-secret.yaml
kubectl apply -f ../../kubernetes-manifests

######################################################################
# This creates a Frontendconfig for HTTP->HTTPS redirection, modifies
# the default frontend Service to be in Internal Loadbalancer
# (default is External) and finally creates the Ingress that uses the
# certificates created above
######################################################################
kubectl apply -f selfsigned-cert-ingress.yaml
