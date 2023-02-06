# Google Managed Prometheus (GMP) on a GKE cluster

This directory contains files essential to setup liveness probes for Bank of Anthos' microservices running in GKE using GMP.

* `blackbox-exporter.yaml` - contains the Deployment definition of [Blackbox exporter](https://github.com/prometheus/blackbox_exporter/).
* `probes.yaml` - contains the GMP PodMonitoring custom resource definitions per microservice. One monitoring configuration per microservice is defined to be run by the  Blackbox exporter.
* `rules.yaml` - contains the GMP Rules custom resource definition.
* `alertmanager.yaml` - contains configuration of Alertmanager to send notifications to Slack channel via Webhook URL.
