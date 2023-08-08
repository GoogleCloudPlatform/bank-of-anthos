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

variable "project_id" {
  type        = string
  description = "Project ID where the resources will be deployed"
}

variable "region" {
  type        = string
  description = "Region where regional resources will be deployed (e.g. us-east1)"
}

variable "zone" {
  type        = string
  description = "Zone for the CloudSQL master instance (e.g. us-east1-b)"
}

variable "sync_repo" {
  type        = string
  description = "Short version of repository to sync ACM configs from & use source for CI (e.g. 'bank-of-anthos' for https://www.github.com/GoogleCloudPlatform/bank-of-anthos)"
}

variable "repo_owner" {
  type        = string
  description = "Github username of the github repo owner whose fork shall be used for ACM, CloudBuild triggers (e.g. 'GoogleCloudPlatform' for https://www.github.com/GoogleCloudPlatform/bank-of-anthos)"
}

variable "sync_branch" {
  type        = string
  description = "Branch to sync ACM configs from & trigger CICD if pushed to."
}
