# TLS with SSL certificate issued by Let's Encrypt

This directory contains configuration of Bank of Anthos application to run it on GKE with TLS Ingress that uses SSL certificates issued by Let's Encrypt.

* `global-ip-and-dns-zone` - directory contians Terraform configuration for Global IP address and Cloud DNS Zone resources.
* `kubernets-manifests` - directory contians Kubernetes manifests of Bank of Anthos application.
* `ssl-certificate` - directory contians Terraform configuration for issues of SSL certificate by Let's Encrypt and store as GCP SSL certificate.

To apply these configurations follow the next order:

* Apply Terraform configuration in `global-ip-and-dns-zone`
* Apply Terraform configuration in `ssl-certificate`
* Apply Kubernetes manifests in `kubernets-manifests`
