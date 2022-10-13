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

# enable ASM feature on fleet
resource "google_gke_hub_feature" "asm" {
  name = "servicemesh"
  location = "global"
  project = var.project_id
  
  provider = google-beta

  depends_on = [
    module.enabled_google_apis
  ]
}

# enable ACM feature on fleet
resource "google_gke_hub_feature" "acm" {
  name = "configmanagement"
  location = "global"
  project = var.project_id
  
  provider = google-beta

  depends_on = [
    module.enabled_google_apis
  ]
}
