#!/bin/bash
set -e

if [ ! -f opsani-manifests-orig.yaml ]; then
  cp opsani-manifests.yaml opsani-manifests-orig.yaml
else
  cp opsani-manifests-orig.yaml opsani-manifests.yaml
fi

source bank-of-anthos.source

awk '{ gsub(A, B); print; }' A="{{ NAMESPACE }}" B="$NAMESPACE" < opsani-manifests.yaml > intermediate-namespace
awk '{ gsub(A, B); print; }' A="{{ DEPLOYMENT }}" B="$DEPLOYMENT" < intermediate-namespace > intermediate-deployment
awk '{ gsub(A, B); print; }' A="{{ SERVICE }}" B="$SERVICE" < intermediate-deployment > intermediate-service
awk '{ gsub(A, B); print; }' A="{{ CONTAINER }}" B="$CONTAINER" < intermediate-service > opsani-manifests.yaml

rm intermediate-*
