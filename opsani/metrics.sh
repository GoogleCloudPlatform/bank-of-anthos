#!/bin/bash

echo "enable standard Kublet derived metrics-service for HPA"

kubectl apply -f k8s-sig-metrics-server-0.4.1-components.yaml
