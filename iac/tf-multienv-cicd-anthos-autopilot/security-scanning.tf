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
  security_remediation_target_branch = "cursor-test"
  security_remediation_min_severity    = "HIGH"
}

resource "google_service_account" "security_remediation" {
  project    = var.project_id
  account_id = "security-remediation"
}

resource "google_project_iam_member" "security_remediation_artifact_analysis" {
  project = var.project_id
  role    = "roles/containeranalysis.occurrences.viewer"
  member  = "serviceAccount:${google_service_account.security_remediation.email}"
}

resource "google_project_iam_member" "security_remediation_cloudbuild_builder" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${google_service_account.security_remediation.email}"
}

resource "google_project_iam_member" "security_remediation_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.security_remediation.email}"
}

resource "google_pubsub_topic" "vulnerability_notifications" {
  project = var.project_id
  name    = "container-vulnerability-notifications"
}

resource "google_pubsub_topic_iam_member" "artifact_analysis_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.vulnerability_notifications.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-artifactanalysis.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription" "vulnerability_notifications" {
  project = var.project_id
  name    = "container-vulnerability-notifications-sub"
  topic   = google_pubsub_topic.vulnerability_notifications.name

  ack_deadline_seconds = 600

  expiration_policy {
    ttl = ""
  }
}

resource "google_secret_manager_secret" "github_app_credentials" {
  project   = var.project_id
  secret_id = "security-remediation-github-app"

  replication {
    auto {}
  }

  depends_on = [
    module.enabled_google_apis
  ]
}

resource "google_secret_manager_secret_iam_member" "security_remediation_github_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.github_app_credentials.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.security_remediation.email}"
}

resource "google_cloudbuild_trigger" "security_remediation" {
  name        = "security-remediation"
  project     = var.project_id
  location    = var.region
  description = "Opens remediation PRs when fixable container vulnerabilities are found"

  github {
    owner = var.repo_owner
    name  = var.sync_repo

    push {
      branch = "^${local.security_remediation_target_branch}$"
    }
  }

  included_files = ["security/remediate/**"]
  filename       = "security/remediate/cloudbuild.yaml"

  substitutions = {
    _CONTAINER_REGISTRY = "${google_artifact_registry_repository.container_registry.location}-docker.pkg.dev/${google_artifact_registry_repository.container_registry.project}/${google_artifact_registry_repository.container_registry.repository_id}"
    _TARGET_BRANCH      = local.security_remediation_target_branch
    _MIN_SEVERITY       = local.security_remediation_min_severity
    _GITHUB_REPO_OWNER  = var.repo_owner
    _GITHUB_REPO_NAME   = var.sync_repo
    _GITHUB_SECRET      = google_secret_manager_secret.github_app_credentials.secret_id
  }

  service_account = google_service_account.security_remediation.id

  depends_on = [
    module.enabled_google_apis
  ]
}

resource "google_cloudbuild_trigger" "security_remediation_pubsub" {
  name        = "security-remediation-vuln-event"
  project     = var.project_id
  location    = var.region
  description = "Runs remediation job when Container Analysis publishes vulnerability updates"

  pubsub_config {
    topic                 = google_pubsub_topic.vulnerability_notifications.id
    service_account_email = google_service_account.security_remediation.email
  }

  source_to_build {
    uri       = local.sync_repo_url
    ref       = "refs/heads/${local.security_remediation_target_branch}"
    repo_type = "GITHUB"
  }

  filename = "security/remediate/cloudbuild.yaml"

  substitutions = {
    _CONTAINER_REGISTRY = "${google_artifact_registry_repository.container_registry.location}-docker.pkg.dev/${google_artifact_registry_repository.container_registry.project}/${google_artifact_registry_repository.container_registry.repository_id}"
    _TARGET_BRANCH      = local.security_remediation_target_branch
    _MIN_SEVERITY       = local.security_remediation_min_severity
    _GITHUB_REPO_OWNER  = var.repo_owner
    _GITHUB_REPO_NAME   = var.sync_repo
    _GITHUB_SECRET      = google_secret_manager_secret.github_app_credentials.secret_id
  }

  service_account = google_service_account.security_remediation.id

  depends_on = [
    module.enabled_google_apis,
    google_pubsub_subscription.vulnerability_notifications
  ]
}

resource "google_project_iam_member" "security_remediation_run_trigger" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.security_remediation.email}"
}

resource "google_cloud_scheduler_job" "security_remediation_daily" {
  project     = var.project_id
  name        = "security-remediation-daily"
  description = "Daily scan of Artifact Registry images for fixable vulnerabilities"
  schedule    = "0 6 * * *"
  time_zone   = "UTC"
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "https://cloudbuild.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/triggers/${google_cloudbuild_trigger.security_remediation_pubsub.trigger_id}:run"

    oauth_token {
      service_account_email = google_service_account.security_remediation.email
    }

    body = base64encode(jsonencode({
      projectId = var.project_id
    }))
  }

  depends_on = [
    google_project_iam_member.security_remediation_run_trigger
  ]
}
