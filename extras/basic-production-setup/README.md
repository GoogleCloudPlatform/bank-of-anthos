# TLS with Google Managed SSL certificate issued by Let's Encrypt

This directory contains configuration of the Bank of Anthos web application to run it on GKE Autopilot with TLS Ingress that uses Google Managed SSL certificates.

* `gke-autopilot` - directory contians Terraform configuration to create GKE Autopilot.
* `ip-and-dns` - directory contians Terraform configuration for Global IP address and Cloud DNS Zone resources.
* `kubernets-manifests` - directory contians Kubernetes manifests of Bank of Anthos application.

To apply these configurations follow the next order:

* Apply Terraform configuration in `gke-autopilot`
* Apply Terraform configuration in `ip-and-dns`
* Apply Kubernetes manifests in `kubernets-manifests`
