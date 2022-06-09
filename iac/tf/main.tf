terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.24.0"
    }
  }
}

variable "registry_name" {
    type = string
    default = "bank-of-anthos"
}

variable "project_id" {
    type = string
    nullable = false
}

variable "region" {
    type = string
    nullable = false
}

variable "zone" {
    type = string
    nullable = false
}

provider "google" {
  // credentials = file("service-account.json") need to add service account here
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  // credentials = file("service-account.json") need to add service account here
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

data "google_project" "project" {
}

resource "google_project_service" "artifactregistry" {
  service                    = "artifactregistry.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "sourcerepo" {
  service                    = "sourcerepo.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "cloudbuild" {
  service                    = "cloudbuild.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "clouddeploy" {
  service                    = "clouddeploy.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "container" {
  service                    = "container.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "compute" {
  service                    = "compute.googleapis.com"
  disable_dependent_services = true
}

resource "google_service_account" "gke_workload" {
  account_id = "gke-workload"
}

resource "google_project_iam_binding" "artifactregistry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com",
    "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  ]

  depends_on = [
    google_project_service.cloudbuild
  ]
}

resource "google_project_iam_binding" "artifactregistry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  members = [
    "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  ]

  depends_on = [
    google_project_service.cloudbuild
  ]
}

resource "google_project_iam_binding" "clouddeploy_releaser" {
  project = var.project_id
  role    = "roles/clouddeploy.releaser"
  members = [
    "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  ]

  depends_on = [
    google_project_service.cloudbuild
  ]
}

resource "google_project_iam_binding" "cloudbuild_builds_builder" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.builder"
  members = [
    "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  ]

  depends_on = [
    google_project_service.cloudbuild
  ]
}

resource "google_project_iam_binding" "container_nodeServiceAgent" {
  project = var.project_id
  role    = "roles/container.nodeServiceAgent"
  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  ]

  depends_on = [
    google_project_service.compute,
    google_project_service.container
  ]
}

resource "google_project_iam_binding" "container_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  ]

  depends_on = [
    google_project_service.compute,
    google_project_service.container
  ]
}

resource "google_project_iam_binding" "storage_objectCreator" {
  project = var.project_id
  role    = "roles/storage.objectCreator"
  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  ]
  depends_on = [
    google_project_service.compute
  ]
}

resource "google_project_iam_binding" "logging_logWriter" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com",
    "serviceAccount:${google_service_account.gke_workload.email}",
    "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  ]

  depends_on = [
    google_project_service.compute,
    google_service_account.gke_workload
  ]
}

resource "google_project_iam_binding" "monitoring_metricWriter" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  members = [
    "serviceAccount:${google_service_account.gke_workload.email}"
  ]

  depends_on = [
    google_project_service.compute
  ]
}

resource "google_storage_bucket" "cache-bucket" {
  name                        = "skaffold-cache-${data.google_project.project.number}"
  uniform_bucket_level_access = true
  location                    = "EU"
}

resource "google_storage_bucket_object" "cache-accounts" {
  name   = "accounts/cache"
  source = "./resources/cache"
  bucket = google_storage_bucket.cache-bucket.name
}

resource "google_storage_bucket_object" "cache-frontend" {
  name   = "frontend/cache"
  source = "./resources/cache"
  bucket = google_storage_bucket.cache-bucket.name
}

resource "google_storage_bucket_object" "cache-ledger" {
  name   = "ledger/cache"
  source = "./resources/cache"
  bucket = google_storage_bucket.cache-bucket.name
}

resource "google_artifact_registry_repository" "docker_repo" {
  provider = google-beta

  location      = "europe-west1"
  repository_id = var.registry_name
  format        = "DOCKER"

  depends_on = [
    google_project_service.artifactregistry
  ]
}

resource "google_sourcerepo_repository" "mirror_repo" {
  name = "bank-of-anthos"

  depends_on = [
    google_project_service.sourcerepo
  ]
}

resource "google_cloudbuild_trigger" "accounts" {
  name = "accounts-ci"
  trigger_template {
    repo_name   = google_sourcerepo_repository.mirror_repo.name
    branch_name = ".*"
  }
  included_files = ["src/accounts/**", "src/components/**"]
  filename       = "cloudbuild.yaml"
  substitutions = {
    _DEPLOY_UNIT        = "accounts"
    _CACHE_URI          = "gs://${google_storage_bucket.cache-bucket.name}/${google_storage_bucket_object.cache-accounts.name}"
    _CONTAINER_REGISTRY = "europe-west1-docker.pkg.dev/${data.google_project.project.project_id}/${var.registry_name}"
  }

  depends_on = [
    google_project_service.cloudbuild
  ]
}

resource "google_cloudbuild_trigger" "frontend" {
  name = "frontend-ci"
  trigger_template {
    repo_name   = google_sourcerepo_repository.mirror_repo.name
    branch_name = ".*"
  }
  included_files = ["src/frontend/**", "src/components/**"]
  filename       = "cloudbuild.yaml"
  substitutions = {
    _DEPLOY_UNIT        = "frontend"
    _CACHE_URI          = "gs://${google_storage_bucket.cache-bucket.name}/${google_storage_bucket_object.cache-frontend.name}"
    _CONTAINER_REGISTRY = "europe-west1-docker.pkg.dev/${data.google_project.project.project_id}/${var.registry_name}"
  }

  depends_on = [
    google_project_service.cloudbuild
  ]
}

resource "google_cloudbuild_trigger" "ledger" {
  name = "ledger-ci"
  trigger_template {
    repo_name   = google_sourcerepo_repository.mirror_repo.name
    branch_name = ".*"
  }
  included_files = ["src/ledger/**", "src/components/**"]
  filename       = "cloudbuild-mvnw.yaml"
  substitutions = {
    _DEPLOY_UNIT        = "ledger"
    _CACHE_URI          = "gs://${google_storage_bucket.cache-bucket.name}/${google_storage_bucket_object.cache-ledger.name}"
    _CONTAINER_REGISTRY = "europe-west1-docker.pkg.dev/${data.google_project.project.project_id}/${var.registry_name}"
  }

  depends_on = [
    google_project_service.cloudbuild
  ]
}

resource "google_compute_network" "development" {
  name                    = "development"
  auto_create_subnetworks = true
  depends_on = [
    google_project_service.compute
  ]
}

resource "google_compute_network" "staging" {
  name                    = "staging"
  auto_create_subnetworks = true
  depends_on = [
    google_project_service.compute
  ]
}

resource "google_compute_network" "production" {
  name                    = "production"
  auto_create_subnetworks = true
  depends_on = [
    google_project_service.compute
  ]
}

resource "google_container_cluster" "development" {
  name             = "development"
  enable_autopilot = true
  network          = google_compute_network.development.self_link
  location         = "europe-west1"
  ip_allocation_policy {

  }
  depends_on = [
    google_project_service.container,
    google_compute_network.development
  ]
}

resource "google_container_cluster" "staging" {
  name             = "staging"
  enable_autopilot = true
  network          = google_compute_network.staging.self_link
  location         = "europe-west1"
  ip_allocation_policy {

  }
  depends_on = [
    google_project_service.container,
    google_compute_network.staging
  ]
}

resource "google_container_cluster" "production" {
  name             = "production"
  enable_autopilot = true
  network          = google_compute_network.production.self_link
  location         = "europe-west1"
  ip_allocation_policy {

  }
  depends_on = [
    google_project_service.container,
    google_compute_network.production
  ]
}

resource "google_clouddeploy_target" "staging" {
  location = "europe-west1"
  name     = "staging"
  gke {
    cluster = google_container_cluster.staging.id
  }

  depends_on = [
    google_project_service.clouddeploy
  ]
}

resource "google_clouddeploy_target" "production" {
  location = "europe-west1"
  name     = "production"
  gke {
    cluster = google_container_cluster.production.id
  }

  depends_on = [
    google_project_service.clouddeploy
  ]
}

resource "google_clouddeploy_delivery_pipeline" "accounts" {
  location = "europe-west1"
  name     = "accounts"
  serial_pipeline {
    stages {
      profiles  = ["staging"]
      target_id = google_clouddeploy_target.staging.name
    }

    stages {
      profiles  = ["production"]
      target_id = google_clouddeploy_target.production.name
    }
  }
}

resource "google_clouddeploy_delivery_pipeline" "frontend" {
  location = "europe-west1"
  name     = "frontend"
  serial_pipeline {
    stages {
      profiles  = ["staging"]
      target_id = google_clouddeploy_target.staging.name
    }

    stages {
      profiles  = ["production"]
      target_id = google_clouddeploy_target.production.name
    }
  }
}

resource "google_clouddeploy_delivery_pipeline" "ledger" {
  location = "europe-west1"
  name     = "ledger"
  serial_pipeline {
    stages {
      profiles  = ["staging"]
      target_id = google_clouddeploy_target.staging.name
    }

    stages {
      profiles  = ["production"]
      target_id = google_clouddeploy_target.production.name
    }
  }
}

resource "google_service_account_iam_binding" "iam_serviceAccountUser_compute" {
  service_account_id = "${data.google_project.project.id}/serviceAccounts/${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  members = [
    "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  ]
  depends_on = [
    google_project_service.compute
  ]
}