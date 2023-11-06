# Copyright 2022 Google LLC
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

# explicit setup of VPC & subnets for GKE resources
module "network" {
  source  = "terraform-google-modules/network/google"
  version = "~> 8.0.0"

  project_id   = var.project_id
  network_name = local.network_name

  subnets = [
    {
      subnet_name           = local.network.development.subnetwork
      subnet_ip             = "10.0.0.0/16"
      subnet_region         = var.region
      subnet_private_access = true
    },
    {
      subnet_name           = local.network.development.master_auth_subnet_name
      subnet_ip             = "10.1.0.0/16"
      subnet_region         = var.region
      subnet_private_access = true
    },
    {
      subnet_name           = local.network.staging.subnetwork
      subnet_ip             = "10.2.0.0/16"
      subnet_region         = var.region
      subnet_private_access = true
    },
    {
      subnet_name           = local.network.staging.master_auth_subnet_name
      subnet_ip             = "10.3.0.0/16"
      subnet_region         = var.region
      subnet_private_access = true
    },
    {
      subnet_name           = local.network.production.subnetwork
      subnet_ip             = "10.4.0.0/16"
      subnet_region         = var.region
      subnet_private_access = true
    },
    {
      subnet_name           = local.network.production.master_auth_subnet_name
      subnet_ip             = "10.5.0.0/16"
      subnet_region         = var.region
      subnet_private_access = true
    },
  ]

  secondary_ranges = {
    (local.network.development.subnetwork) = [
      {
        range_name    = local.network.development.ip_range_pods
        ip_cidr_range = "172.16.0.0/16"
      },
      {
        range_name    = local.network.development.ip_range_services
        ip_cidr_range = "172.17.0.0/16"
    }, ]
    (local.network.staging.subnetwork) = [
      {
        range_name    = local.network.staging.ip_range_pods
        ip_cidr_range = "172.18.0.0/16"
      },
      {
        range_name    = local.network.staging.ip_range_services
        ip_cidr_range = "172.19.0.0/16"
    }, ]
    (local.network.production.subnetwork) = [{
      range_name    = local.network.production.ip_range_pods
      ip_cidr_range = "172.20.0.0/16"
      },
      {
        range_name    = local.network.production.ip_range_services
        ip_cidr_range = "172.21.0.0/16"
      },
    ]
  }

  depends_on = [
    module.enabled_google_apis
  ]
}
