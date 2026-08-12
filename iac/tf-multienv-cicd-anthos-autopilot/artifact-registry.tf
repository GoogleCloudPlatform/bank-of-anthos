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

# create artifact registry for container images
resource "google_artifact_registry_repository" "container_registry" {
  repository_id = local.application_name
  location      = var.region
  format        = "docker"
  description   = "Bank of Anthos docker repository"
  project       = var.project_id

  depends_on = [
    module.enabled_google_apis
  ]
}

# we cannot use a custom service account with autopilot clusters in terraform https://github.com/hashicorp/terraform-provider-google/issues/9505 🤷
# so we're using the default compute service account here...
module "artifact-registry-repository-iam-bindings" {
  source       = "terraform-google-modules/iam/google//modules/artifact_registry_iam"
  project      = var.project_id
  repositories = [local.application_name]
  location     = var.region
  mode         = "authoritative"

  bindings = {
    "roles/artifactregistry.reader" = [
      "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com",
      "serviceAccount:${google_service_account.cloud_deploy.email}"
    ],
    "roles/artifactregistry.writer" = [
      "serviceAccount:${google_service_account.cloud_build_pr.email}"
    ]

  }

  depends_on = [
    module.enabled_google_apis,
    google_artifact_registry_repository.container_registry
  ]
}
