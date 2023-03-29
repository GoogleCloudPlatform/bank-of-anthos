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

# cloud build service account
resource "google_service_account" "cloud_build" {
  project    = var.project_id
  account_id = "ci-${local.service_name}"
}

# additional roles for cloud-build service account
resource "google_artifact_registry_repository_iam_member" "cloud_build" {
  repository = var.container_registry.repository_id
  location   = var.container_registry.location
  project    = var.container_registry.project

  role   = "roles/artifactregistry.writer"
  member = "serviceAccount:${google_service_account.cloud_build.email}"

  provider = google-beta
}

resource "google_service_account_iam_member" "cloud_build_impersonate_cloud_deploy" {
  service_account_id = var.cloud_deploy_sa.id
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloud_build.email}"
}

