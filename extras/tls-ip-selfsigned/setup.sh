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

# Delete frontend svc type loadbalancer 
kubectl delete svc frontend 

# Create service type nodeport 
# (this will still allow in-cluster traffic from the loadgen because nodeport services automatically spawn cluster IP services)
kubectl apply -f frontend-nodeport.yaml 


# Apply frontend config to allow HTTP -> HTTPS redirect 
kubectl apply -f frontend-config.yaml

# Create ingress, referencing the cert secret and static IP 
kubectl apply -f frontend-ingress.yaml