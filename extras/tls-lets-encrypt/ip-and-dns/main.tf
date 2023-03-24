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
}

provider "google" {}

variable "base_domin" {
  type        = string
  description = "Your base domain"
}

variable "name" {
  type        = string
  description = "Name of resources"
  default     = "bank-of-anthos"
}

resource "google_compute_global_address" "default" {
  name = var.name
}

resource "google_dns_managed_zone" "default" {
  name        = var.name
  dns_name    = "${var.name}.${var.base_domin}."
  description = "DNS Zone for Bank of Anthos sample web application"
}

resource "google_dns_record_set" "a" {
  name         = google_dns_managed_zone.default.dns_name
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.default.name

  rrdatas = [google_compute_global_address.default.address]
}

resource "google_dns_record_set" "cname" {
  name         = join(".", compact(["www", google_dns_record_set.a.name]))
  type         = "CNAME"
  ttl          = 300
  managed_zone = google_dns_managed_zone.default.name

  rrdatas = [google_dns_record_set.a.name]
}

output "dns_zone_name_servers" {
  value       = google_dns_managed_zone.default.name_servers
  description = "Write these virtual name servers in your base domain."
}

output "domain" {
  value = trim(google_dns_record_set.a.name, ".")
}
