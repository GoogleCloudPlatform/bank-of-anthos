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

# GCS bucket used as skaffold build cache
resource "google_storage_bucket" "build_cache" {
  name                        = "build-cache-${var.team}-${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
}

# GCS bucket used by Cloud Build to stage sources for Cloud Deploy
resource "google_storage_bucket" "release_source_staging" {
  name                        = "release-source-staging-${var.team}-${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
}

# GCS bucket used by Cloud Deploy for delivery artifact storage
resource "google_storage_bucket" "delivery_artifacts" {
  name                        = "delivery-artifacts-${var.team}-${var.project_id}"
  uniform_bucket_level_access = true
  location                    = var.region
}

# Initialize cache with empty file
resource "google_storage_bucket_object" "cache" {
  bucket = google_storage_bucket.build_cache.name

  name   = local.cache_filename
  content = " "

  lifecycle {
    # do not reset cache when running terraform
    ignore_changes = [
        content,
        detect_md5hash
    ]
  }
}

# give CloudBuild SA access to skaffold cache
resource "google_storage_bucket_iam_member" "build_cache" {
  bucket = google_storage_bucket.build_cache.name

  member = "serviceAccount:${google_service_account.cloud_build.email}"
  role = "roles/storage.admin"
}

# give CloudBuild SA access to write to source staging bucket
resource "google_storage_bucket_iam_member" "release_source_staging_admin" {
  bucket = google_storage_bucket.release_source_staging.name

  member = "serviceAccount:${google_service_account.cloud_build.email}"
  role = "roles/storage.admin"
}

# give CloudDeploy SA access to read from source staging bucket
resource "google_storage_bucket_iam_member" "release_source_staging_objectViewer" {
  bucket = google_storage_bucket.release_source_staging.name

  member = "serviceAccount:${google_service_account.cloud_deploy.email}"
  role = "roles/storage.objectViewer"
}

# give CloudDeploy SA access to administrate to delivery artifact bucket
resource "google_storage_bucket_iam_member" "delivery_artifacts" {
  bucket = google_storage_bucket.delivery_artifacts.name

  member = "serviceAccount:${google_service_account.cloud_deploy.email}"
  role = "roles/storage.admin"
}