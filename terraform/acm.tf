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

resource "google_gke_hub_feature" "configmanagement_acm_feature" {
  provider = google-beta
  name     = "configmanagement"
  location = "global"
  depends_on = [
    module.boa-secret
  ]
}

resource "google_gke_hub_feature_membership" "membership" {
  provider   = google-beta
  location   = "global"
  feature    = "configmanagement"
  membership = "${module.gke.name}-membership"
  configmanagement {
    config_sync {
      source_format = "unstructured"
      git {
        sync_repo   = var.sync_repo
        sync_branch = var.sync_branch
        sync_rev    = var.sync_rev
        policy_dir  = var.policy_dir
        secret_type = "none"
      }
    }
  }
  depends_on = [
    google_gke_hub_feature.configmanagement_acm_feature
  ]
}
