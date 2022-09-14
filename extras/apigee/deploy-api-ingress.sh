#!/bin/bash

# Copyright 2022 Google LLC
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

set -e

if [ -z "$PROJECT" ]
then
echo "No PROJECT variable set"
exit
fi

if [ -z "$REGION" ]
then
echo "No REGION variable set"
exit
fi

if [ -z "$ZONE" ]
then
echo "No ZONE variable set"
exit
fi

if [ -z "$CLUSTERNAME" ]
then
echo "No CLUSTERNAME variable set"
exit
fi

if [ -z "$BOA_NAMESPACE" ]
then
echo "No BOA_NAMESPACE variable set"
exit
fi

gcloud container clusters get-credentials $CLUSTERNAME \
--project=$PROJECT \
--zone=$ZONE

kubectl config set-context $CLUSTERNAME

ASM_VERSION=$(kubectl get deploy -n istio-system -l app=istiod -o jsonpath={.items[*].metadata.labels.'istio\.io\/rev'}'{"\n"}')
kubectl label namespace "${BOA_NAMESPACE}" istio.io/rev=$ASM_VERSION --overwrite

kubectl apply -n "${BOA_NAMESPACE}" -f  ./api-ingress/kubernetes-manifests/deployment.yaml

kubectl apply -n "${BOA_NAMESPACE}" -f ./api-ingress/kubernetes-manifests/serviceaccount.yaml

kubectl apply -n "${BOA_NAMESPACE}" -f ./api-ingress/kubernetes-manifests/role.yaml

kubectl apply -n "${BOA_NAMESPACE}" -f ./api-ingress/kubernetes-manifests/service.yaml

kubectl apply -n "${BOA_NAMESPACE}" -f ./api-ingress/kubernetes-manifests/istio-gateway.yaml