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
  alias                  = "production"
  host                   = "https://${module.gke_production.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke_production.ca_certificate)
}

# production autopilot cluster
module "gke_production" {
  source = "terraform-google-modules/kubernetes-engine/google//modules/beta-autopilot-private-cluster"
  version = "29.0.0"

  project_id              = var.project_id
  name                    = "production"
  regional                = true
  region                  = var.region
  network                 = local.network_name
  subnetwork              = local.network.production.subnetwork
  ip_range_pods           = local.network.production.ip_range_pods
  ip_range_services       = local.network.production.ip_range_services
  enable_private_nodes    = true
  enable_private_endpoint = true
  master_authorized_networks = [{
    cidr_block   = module.network.subnets["${var.region}/${local.network.production.master_auth_subnet_name}"].ip_cidr_range
    display_name = local.network.production.subnetwork
  }]
  master_ipv4_cidr_block          = "10.6.0.16/28"
  release_channel                 = "RAPID"
  enable_vertical_pod_autoscaling = true
  horizontal_pod_autoscaling      = true
  create_service_account          = false # currently not supported by terraform for autopilot clusters
  cluster_resource_labels         = { "mesh_id" : "proj-${data.google_project.project.number}" }

  providers = {
    kubernetes = kubernetes.production
  }

  depends_on = [
    module.enabled_google_apis,
    module.network,
    google_gke_hub_feature.asm,
    google_gke_hub_feature.acm
  ]
}

# production GKE workload GSA
resource "google_service_account" "gke_workload_production" {
  account_id = "gke-workload-production"
}

# binding production GKE workload GSA to KSA
resource "google_service_account_iam_member" "gke_workload_production_identity" {
  service_account_id = google_service_account.gke_workload_production.id
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[bank-of-anthos-production/bank-of-anthos]"
  depends_on = [
    module.gke_production
  ]
}

# CloudSQL Postgres production instance
module "cloudsql_production" {
  source  = "GoogleCloudPlatform/sql-db/google//modules/postgresql"
  version = "~> 20.0.0"

  project_id = var.project_id
  region     = var.region

  name                = "${local.application_name}-db-production"
  database_version    = "POSTGRES_14"
  enable_default_db   = false
  tier                = "db-custom-1-3840"
  deletion_protection = false
  availability_type   = "REGIONAL"
  zone                = var.zone

  additional_databases = [
    {
      name      = "accounts-db"
      charset   = ""
      collation = ""
    },
    {
      name      = "ledger-db"
      charset   = ""
      collation = ""
    }
  ]
  user_name     = "admin"
  user_password = "admin" # this is a security risk - do not do this for real world use-cases!
}

# create fleet membership for production GKE cluster
resource "google_gke_hub_membership" "production" {
  provider      = google-beta
  project       = var.project_id
  membership_id = "production-membership"
  endpoint {
    gke_cluster {
      resource_link = "//container.googleapis.com/${module.gke_production.cluster_id}"
    }
  }
  authority {
    issuer = "https://container.googleapis.com/v1/${module.gke_production.cluster_id}"
  }
}

# configure ASM for production GKE cluster
resource "google_gke_hub_feature_membership" "asm_production" {
  project  = var.project_id
  location = "global"

  feature    = google_gke_hub_feature.asm.name
  membership = google_gke_hub_membership.production.membership_id
  mesh {
    management = "MANAGEMENT_AUTOMATIC"
  }
  provider = google-beta
}

# configure ACM for production GKE cluster
resource "google_gke_hub_feature_membership" "acm_production" {
  project  = var.project_id
  location = "global"

  feature    = google_gke_hub_feature.acm.name
  membership = google_gke_hub_membership.production.membership_id
  configmanagement {
    config_sync {
      git {
        sync_repo   = local.sync_repo_url
        sync_branch = var.sync_branch
        policy_dir  = "iac/acm-multienv-cicd-anthos-autopilot/overlays/production"
        secret_type = "none"
      }
      source_format = "unstructured"
    }
  }
  provider = google-beta
}

resource "google_compute_global_address" "production_ip" {
  name = "bank-of-anthos-ip" # hardcoded in frontend ingress k8s manifest

  depends_on = [
    module.enabled_google_apis,
  ]
}

resource "google_compute_security_policy" "production_security_policy" {
  name        = "bank-of-anthos-security-policy" # hardcoded in backendconfig k8s manifest
  description = "Block various attacks against bank of anthos production deployment"

  rule {
    description = "XSS attack filtering"
    priority    = "1000"
    action      = "deny(403)"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-stable')"
      }
    }
  }

  rule {
    description = "CVE-2021-44228 and CVE-2021-45046"
    priority    = "12345"
    action      = "deny(403)"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('cve-canary')"
      }
    }
  }

  rule {
    description = "default rule"
    priority    = "2147483647"
    action      = "allow"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }

  adaptive_protection_config {
    layer_7_ddos_defense_config {
      enable = true
    }
  }

  advanced_options_config {
    log_level = "VERBOSE"
  }

  depends_on = [
    module.enabled_google_apis,
  ]
}

resource "google_compute_ssl_policy" "production_ssl_policy" {
  name            = "bank-of-anthos-ssl-policy" # hardcoded in frontendconfig k8s manifest
  profile         = "COMPATIBLE"
  min_tls_version = "TLS_1_0" # TODO: consider increasing this

  depends_on = [
    module.enabled_google_apis,
  ]
}
