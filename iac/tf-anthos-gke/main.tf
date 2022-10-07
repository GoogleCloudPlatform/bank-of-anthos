/**
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

data "google_project" "project" {
  project_id = var.project
}

data "google_client_config" "default" {}

module "enabled_google_apis" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "~> 14.0"

  project_id                  = data.google_project.project.project_id
  disable_services_on_destroy = false

  activate_apis = [
    "compute.googleapis.com",
    "anthos.googleapis.com",
    "container.googleapis.com",
    "gkehub.googleapis.com",
    "gkeconnect.googleapis.com",
    "anthosconfigmanagement.googleapis.com",
    "mesh.googleapis.com",
    "meshconfig.googleapis.com",
    "meshtelemetry.googleapis.com",
  ]
}