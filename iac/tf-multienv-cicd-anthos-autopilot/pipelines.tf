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
  for_each = toset(local.services)

  project_id = var.project_id
  region = var.region
  container_registry = google_artifact_registry_repository.container_registry
  repo_owner = var.repo_owner
  repo_name = var.sync_repo
  service = each.value
  targets = [google_clouddeploy_target.staging, google_clouddeploy_target.production]
  repo_branch = var.sync_branch
  cloud_deploy_sa = google_service_account.cloud_deploy

  depends_on = [
    module.enabled_google_apis
  ]
}

# cloud deploy service account
resource "google_service_account" "cloud_deploy" {
  project    = var.project_id
  account_id = "cloud-deploy"
}

resource "google_clouddeploy_target" "staging" {
  # one CloudDeploy target per target defined in vars

  project  = var.project_id
  name     = "staging"
  location = var.region

  anthos_cluster {
    membership = google_gke_hub_membership.staging.id
  }

  execution_configs {
    artifact_storage = "gs://${google_storage_bucket.delivery_artifacts_staging.name}"
    service_account  = google_service_account.cloud_deploy.email
    usages = [
      "RENDER",
      "DEPLOY"
    ]
  }
}

resource "google_clouddeploy_target" "production" {
  # one CloudDeploy target per target defined in vars

  project  = var.project_id
  name     = "production"
  location = var.region

  anthos_cluster {
    membership = google_gke_hub_membership.production.id
  }

  execution_configs {
    artifact_storage = "gs://${google_storage_bucket.delivery_artifacts_production.name}"
    service_account  = google_service_account.cloud_deploy.email
    usages = [
      "RENDER",
      "DEPLOY",
      "VERIFY"
    ]
  }
}


# GCS bucket used by Cloud Deploy for delivery artifact storage
resource "google_storage_bucket" "delivery_artifacts_staging" {
  project                     = var.project_id
  name                        = "delivery-artifacts-staging-${data.google_project.project.number}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # Explicitly set to true
}

# GCS bucket used by Cloud Deploy for delivery artifact storage
resource "google_storage_bucket" "delivery_artifacts_production" {
  project                     = var.project_id
  name                        = "delivery-artifacts-production-${data.google_project.project.number}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # Explicitly set to true
}

# give CloudDeploy SA access to administrate to delivery artifact bucket
resource "google_storage_bucket_iam_member" "delivery_artifacts_staging" {
  bucket  = google_storage_bucket.delivery_artifacts_staging.name

  member = "serviceAccount:${google_service_account.cloud_deploy.email}"
  role   = "roles/storage.admin"
}

# give CloudDeploy SA access to administrate to delivery artifact bucket
resource "google_storage_bucket_iam_member" "delivery_artifacts_production" {
  bucket  = google_storage_bucket.delivery_artifacts_production.name

  member = "serviceAccount:${google_service_account.cloud_deploy.email}"
  role   = "roles/storage.admin"
}

### CI-PR pipeline

# GCS bucket used as skaffold build cache
resource "google_storage_bucket" "build_cache_pr" {
  name                        = "build-cache-pr-${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
  force_destroy               = true # Explicitly set to true
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

# CI trigger configuration
resource "google_cloudbuild_trigger" "ci-pr" {
  name = "pull-request-ci"
  location = var.region

  github {
      owner = var.repo_owner
      name = var.sync_repo

      pull_request {
        branch = ".*"
        comment_control = "COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY"
      }
  }
  filename = ".github/cloudbuild/ci-pr.yaml"
  substitutions = {
      _CACHE_URI = "gs://${google_storage_bucket.build_cache_pr.name}/${google_storage_bucket_object.cache.name}"
      _CONTAINER_REGISTRY = "${google_artifact_registry_repository.container_registry.location}-docker.pkg.dev/${google_artifact_registry_repository.container_registry.project}/${google_artifact_registry_repository.container_registry.repository_id}"
      _CACHE = local.cache_filename
  }
  service_account = google_service_account.cloud_build_pr.id
}
