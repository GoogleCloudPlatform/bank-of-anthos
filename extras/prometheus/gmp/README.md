# GMP on GKE cluster

This directory contains files related to configuring probing of Bank of Anthos' microservices with GMP on GKE

* `blackbox-exporter.yaml` - Deployment manifest of [Blackbox exporter](https://github.com/prometheus/blackbox_exporter/)
* `probes.yaml` - File contains GMP PodMonitoring custom resource which scrape metrics from Blackbox Exporter with configuration for each microservice.
* `rules.yaml` - File contains GMP Rules custom resource
* `alertmanager.yaml` - File contains configuration of Alertmanager to send notifications to Slack channel via Webhook URL.
