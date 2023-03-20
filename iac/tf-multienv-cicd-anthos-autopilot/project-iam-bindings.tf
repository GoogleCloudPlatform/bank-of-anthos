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

# authoritative project-iam-bindings to increase reproducibility
module "project-iam-bindings" {
  source   = "terraform-google-modules/iam/google//modules/projects_iam"
  projects = [var.project_id]
  mode     = "authoritative"

  bindings = {
    "roles/cloudtrace.agent" = [
      "serviceAccount:${google_service_account.gke_workload_development.email}",
      "serviceAccount:${google_service_account.gke_workload_staging.email}",
      "serviceAccount:${google_service_account.gke_workload_production.email}",
      "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
    ],
    "roles/monitoring.metricWriter" = [
      "serviceAccount:${google_service_account.gke_workload_development.email}",
      "serviceAccount:${google_service_account.gke_workload_staging.email}",
      "serviceAccount:${google_service_account.gke_workload_production.email}",
      "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
    ],
    "roles/logging.logWriter" = setunion(
      [
        "serviceAccount:${google_service_account.gke_workload_development.email}",
        "serviceAccount:${google_service_account.gke_workload_staging.email}",
        "serviceAccount:${google_service_account.gke_workload_production.email}",
        "serviceAccount:${google_service_account.cloud_build_pr.email}",
        "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com",
        "serviceAccount:${google_service_account.cloud_deploy.email}"
      ],
      local.cloud_build_sas
    ),
    "roles/cloudbuild.builds.builder" = setunion(
      [
        "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com",
        "serviceAccount:${google_service_account.cloud_build_pr.email}",
      ],
      local.cloud_build_sas
    ),
    "roles/gkehub.gatewayEditor" = [
      "serviceAccount:${google_service_account.cloud_build_pr.email}",
      "serviceAccount:${google_service_account.cloud_deploy.email}"
    ],
    "roles/gkehub.viewer" = setunion(
      local.cloud_build_sas,
      [
        "serviceAccount:${google_service_account.cloud_build_pr.email}",
        "serviceAccount:${google_service_account.cloud_deploy.email}"
      ],
    ),
    "roles/clouddeploy.releaser" = local.cloud_build_sas,
    "roles/container.developer" = [
      "serviceAccount:${google_service_account.cloud_build_pr.email}",
      "serviceAccount:${google_service_account.cloud_deploy.email}"
    ],
    "roles/cloudsql.client" = [
      "serviceAccount:${google_service_account.gke_workload_staging.email}",    # this implies that staging service account also has access to production CloudSQL. Could be solved by putting the CloudSQL instances in separate projects,
      "serviceAccount:${google_service_account.gke_workload_production.email}", # this implies that production service account also has access to staging CloudSQL. Could be solved by putting the CloudSQL instances in separate projects.
    ],
    "roles/cloudsql.instanceUser" = [
      "serviceAccount:${google_service_account.gke_workload_staging.email}",    # this implies that staging service account also has access to production CloudSQL. Could be solved by putting the CloudSQL instances in separate projects,
      "serviceAccount:${google_service_account.gke_workload_production.email}", # this implies that production service account also has access to staging CloudSQL. Could be solved by putting the CloudSQL instances in separate projects.
    ]
  }
}
