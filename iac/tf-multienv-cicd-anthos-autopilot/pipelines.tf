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

# user-defined module setting up a CloudBuild + CloudDeploy CICD pipeline
module "ci-cd-pipeline" {
  source = "./modules/ci-cd-pipeline"

  # create CICD pipeline per team
  for_each = toset(local.teams)

  project_id = var.project_id
  region = var.region
  container_registry = google_artifact_registry_repository.container_registry
  repo_owner = var.repo_owner
  repo_name = var.sync_repo
  team = each.value
  cluster_memberships = local.cluster_memberships
  targets = local.targets
  repo_branch = var.sync_branch

  depends_on = [
    module.enabled_google_apis
  ]
}

# GCS bucket used as skaffold build cache
resource "google_storage_bucket" "build_cache_pr" {
  name                        = "build-cache-pr-${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true
}

# Initialize cache with empty file
resource "google_storage_bucket_object" "cache" {
  bucket = google_storage_bucket.build_cache_pr.name

  name    = local.cache_filename
  content = " "

  lifecycle {
    # do not reset cache when running terraform
    ignore_changes = [
      content,
      detect_md5hash
    ]
  }
}

# service_account for PRs
resource "google_service_account" "cloud_build_pr" {
  account_id = "cloud-build-pr"
}

# give CloudBuild SA access to skaffold cache
resource "google_storage_bucket_iam_member" "build_cache" {
  bucket = google_storage_bucket.build_cache_pr.name

  member = "serviceAccount:${google_service_account.cloud_build_pr.email}"
  role   = "roles/storage.admin"
}

# additional roles for cloud-build service account
resource "google_artifact_registry_repository_iam_member" "cloud_build" {
  repository = google_artifact_registry_repository.container_registry.repository_id
  location   = google_artifact_registry_repository.container_registry.location
  project    = google_artifact_registry_repository.container_registry.project

  role   = "roles/artifactregistry.writer"
  member = "serviceAccount:${google_service_account.cloud_build_pr.email}"

  provider = google-beta
}