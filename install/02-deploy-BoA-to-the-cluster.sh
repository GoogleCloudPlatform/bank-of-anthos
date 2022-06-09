#!/bin/bash

# Created with codelabba.rb v.1.4a
source .env.sh || fatal 'Couldnt source this'
set -x
set -e

# Add your code here:

# Note: Changed ./ to ../ from README
kubectl apply -f ../extras/jwt/jwt-secret.yaml
kubectl apply -f ../kubernetes-manifests


kubectl get pods




# End of your code here
echo All good.
