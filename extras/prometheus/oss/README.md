# OSS Prometheus on a GKE cluster

This directory contains files essential to setup liveness probes for Bank of Anthos' microservices running in GKE using OSS Prometheus.

* `values.yaml` - contains the configurations for the [OSS Prometheus helm chart](https://github.com/bitnami/charts/tree/main/bitnami/kube-prometheus)
* `probes.yaml` - contains the Probe custom resource definitions per microservice. One monitoring configuration per microservice is defined.
* `rules.yaml` - contains the PrometheusRule custom resource definition.
* `alertmanagerconfig.yaml` - File contain AlertmanagerConfig custom resource with configuration of Alertmanager to send notifications to Slack channel via Webhook URL.
