#!/bin/bash
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gke_tls_ip_selfsigned_setup]
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

# Modify the frontend service to use an Internal LoadBalancer to disallow public traffic
kubectl apply -f frontend-service.yaml

# Apply frontend config to allow HTTP -> HTTPS redirect
kubectl apply -f frontend-config.yaml

# Create ingress, referencing the cert secret and static IP
kubectl apply -f frontend-ingress.yaml

# [END gke_tls_ip_selfsigned_setup]