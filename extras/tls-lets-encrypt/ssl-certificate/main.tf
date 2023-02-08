# Copyright 2023 Google LLC
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

terraform {
  required_version = "~> 1.3"

  required_providers {
    acme = {
      source  = "vancluever/acme"
      version = "~> 2.12.0"
    }
  }
}

provider "google" {}

provider "acme" {
  server_url = "https://acme-staging-v02.api.letsencrypt.org/directory"
  # server_url = "https://acme-v02.api.letsencrypt.org/directory"
}

variable "domin_name" {
  type        = string
  description = "Your domain name"
}

variable "user_email" {
  type        = string
  description = "Your email"
}

data "google_client_config" "current" {}

resource "tls_private_key" "default" {
  algorithm = "RSA"
}

resource "acme_registration" "default" {
  account_key_pem = tls_private_key.default.private_key_pem
  email_address   = var.user_email
}

resource "acme_certificate" "default" {
  account_key_pem           = acme_registration.default.account_key_pem
  common_name               = var.domin_name
  subject_alternative_names = ["*.${var.domin_name}"]

  dns_challenge {
    provider = "gcloud"

    config = {
      GCE_PROJECT = data.google_client_config.current.project
    }
  }

  depends_on = [acme_registration.default]
}

resource "google_compute_ssl_certificate" "default" {
  name        = "soup-to-nuts"
  description = "SSL Certificate issued by Let's Encrypt"
  private_key = acme_certificate.default.private_key_pem
  certificate = acme_certificate.default.certificate_pem

  lifecycle {
    create_before_destroy = true
  }
}

output "ssl_certificate_name" {
  value = google_compute_ssl_certificate.default.name
}
