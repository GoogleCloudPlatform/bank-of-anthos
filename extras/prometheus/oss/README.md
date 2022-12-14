# OSS Prometheus on GKE cluster

This directory contains files related to configuring probing of Bank of Anthos' microservices with OSS Prometheus on GKE.

* `values.yaml` - Configuration file to [OSS Prometheus helm chart](https://github.com/bitnami/charts/tree/main/bitnami/kube-prometheus)
* `probes.yaml` - File contains Probe custom resource manifests for each microservice
* `rules.yaml` - File contains PrometheusRule custom resource
* `alertmanagerconfig.yaml` - File contain AlertmanagerConfig custom resource with configuration of Alertmanager to send notifications to Slack channel via Webhook URL.
