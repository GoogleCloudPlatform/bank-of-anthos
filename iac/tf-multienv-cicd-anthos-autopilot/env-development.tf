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

# Cloud Foundation Toolkit GKE module requires cluster-specific kubernetes provider
provider "kubernetes" {
  alias                  = "development"
  host                   = "https://${module.gke_development.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke_development.ca_certificate)
}

# development autopilot cluster
module "gke_development" {
  source = "terraform-google-modules/kubernetes-engine/google//modules/beta-autopilot-public-cluster"

  project_id        = var.project_id
  name              = "development"
  regional          = true
  region            = var.region
  network           = local.network_name
  subnetwork        = local.network.development.subnetwork
  ip_range_pods     = local.network.development.ip_range_pods
  ip_range_services = local.network.development.ip_range_services
  release_channel                 = "RAPID"
  enable_vertical_pod_autoscaling = true
  horizontal_pod_autoscaling      = true
  create_service_account          = false # currently not supported by terraform for autopilot clusters
  cluster_resource_labels         = { "mesh_id" : "proj-${data.google_project.project.number}" }
  datapath_provider               = "ADVANCED_DATAPATH"

  providers = {
    kubernetes = kubernetes.development
  }

  depends_on = [
    module.enabled_google_apis,
    module.network,
    google_gke_hub_feature.asm,
    google_gke_hub_feature.acm
  ]
}

# development GKE workload GSA
resource "google_service_account" "gke_workload_development" {
  account_id = "gke-workload-development"
}

# binding development GKE workload GSA to KSA
resource "google_service_account_iam_member" "gke_workload_development_identity" {
  service_account_id = google_service_account.gke_workload_development.id
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[bank-of-anthos-development/bank-of-anthos]"
  depends_on = [
    module.gke_development
  ]
}

# create fleet membership for development GKE cluster
resource "google_gke_hub_membership" "development" {
  provider      = google-beta
  project       = var.project_id
  membership_id = "development-membership"
  endpoint {
    gke_cluster {
      resource_link = "//container.googleapis.com/${module.gke_development.cluster_id}"
    }
  }
  authority {
    issuer = "https://container.googleapis.com/v1/${module.gke_development.cluster_id}"
  }
}

# configure ASM for development GKE cluster
module "asm-development" {
    source = "terraform-google-modules/gcloud/google"

    platform = "linux"
    
    create_cmd_entrypoint = "gcloud"
    create_cmd_body = "container fleet mesh update --management automatic --memberships ${google_gke_hub_membership.development.membership_id} --project ${var.project_id}"
    destroy_cmd_entrypoint = "gcloud"
    destroy_cmd_body = "container fleet mesh update --management manual --memberships ${google_gke_hub_membership.development.membership_id} --project ${var.project_id}"
}

# configure ACM for development GKE cluster
module "acm-development" {
  source = "terraform-google-modules/kubernetes-engine/google//modules/acm"

  project_id                = var.project_id
  cluster_name              = module.gke_development.name
  cluster_membership_id     = "development-membership"
  location                  = module.gke_development.location
  sync_repo                 = local.sync_repo_url
  sync_branch               = var.sync_branch
  enable_fleet_feature      = false
  enable_fleet_registration = false
  policy_dir                = "iac/acm-multienv-cicd-anthos-autopilot/overlays/development"
  source_format             = "unstructured"

  depends_on = [
    module.asm-development
  ]

  providers = {
    kubernetes = kubernetes.development
  }
}
