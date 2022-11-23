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

locals {
  teams = ["frontend", "accounts", "ledger"] # List of team names as string
  targets = ["staging", "production"] # List of targets for delivery in order of deployment stages
  application_name = "bank-of-anthos" # used for naming of resources
  cluster_names    = toset(["development", "staging", "production"]) # used to create network configuration below
  network_name     = "shared-gke" # VPC containing resources will be given this name
  network = { for name in local.cluster_names : name =>
    {
      subnetwork              = "${name}-gke-subnet"
      master_auth_subnet_name = "${name}-gke-master-auth-subnet"
      ip_range_pods           = "${name}-ip-range-pods"
      ip_range_services       = "${name}-ip-range-svc"
  } }
  clusters = { # maps cluster_names to tf resources for pipeline configuration
    "development" = module.gke_development
    "staging"     = module.gke_staging
    "production"  = module.gke_production
  }
  sync_repo_url    = "https://www.github.com/${var.repo_owner}/${var.sync_repo}" # repository containing source
  cloud_build_sas  = [for team in local.teams : module.ci-cd-pipeline[team].cloud_build_sa] # cloud build service accounts used for CI
  cloud_deploy_sas = [for team in local.teams : module.ci-cd-pipeline[team].cloud_deploy_sa] # cloud build service accounts used for CD
}
