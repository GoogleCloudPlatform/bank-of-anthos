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

module "acm" {
  source                   = "terraform-google-modules/kubernetes-engine/google//modules/acm"
  version                  = "~> 23.0"
  project_id               = data.google_project.project.project_id
  location                 = module.gke.location
  cluster_name             = module.gke.name
  configmanagement_version = "1.12.2"

  sync_repo     = var.sync_repo
  sync_branch   = var.sync_branch
  sync_revision = var.sync_rev
  policy_dir    = var.policy_dir
  source_format = "unstructured"

  secret_type = "none"
}