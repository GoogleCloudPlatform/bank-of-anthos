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

terraform {
  backend "gcs" {
    bucket = "bank-of-anthos-tf-state"
    prefix = "bank-of-anthos"
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.43.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.43.0"
    }
  }
}

# google-beta provider retained for version pinning
provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# default google provider for most resources
provider "google" {
  project = var.project_id
  region  = var.region
}

# used to get project number
data "google_project" "project" {
}

# data needed for kubernetes provider
data "google_client_config" "default" {}
