/**
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

module "gke" {
  source                   = "terraform-google-modules/kubernetes-engine/google"
  version                  = "~> 23.0"
  project_id               = data.google_project.project.project_id
  name                     = var.cluster_name
  region                   = var.region
  zones                    = [var.zone]
  initial_node_count       = 1
  remove_default_node_pool = true
  network                  = "default"
  subnetwork               = "default"
  ip_range_pods            = ""
  ip_range_services        = ""
  cluster_resource_labels = {
    "mesh_id" : "proj-${data.google_project.project.number}",
  }
  identity_namespace = "${data.google_project.project.project_id}.svc.id.goog"

  node_pools = [
    {
      name         = "asd-node-pool"
      autoscaling  = true
      node_count   = 3
      min_count    = 1
      max_count    = 10
      auto_upgrade = true
      machine_type = "e2-standard-2"
    },
  ]

  depends_on = [
    module.enabled_google_apis
  ]
}

provider "kubernetes" {
  host                   = "https://${module.gke.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.ca_certificate)
}