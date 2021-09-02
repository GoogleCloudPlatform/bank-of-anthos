#!/bin/bash

echo "Add the helm repo for prometheus and grafana"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

echo create the metrics namespace and install prometheus and grafana
kubectl create ns metrics
helm install prometheus prometheus-community/prometheus --namespace metrics
helm install prom-adapter prometheus-community/prometheus-adapter --namespace metrics --values prom-adapter-values.yaml
helm install grafana grafana/grafana --namespace metrics --values grafana-values.yaml

#echo "Add additional metrics for prometheus"
#kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

echo "check metrics availability with: kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1"

