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
    type = string
    description = "Project ID where the resources will be deployed"
}

variable "region" {
    type = string
    description = "Region where regional resources will be deployed"
}

variable "container_registry" {
    type = object({
        location = string
        project = string
        repository_id = string
    })
    description = "Container registry object"
}

variable "repo_owner" {
    type = string
    description = "Owner of the repo that contains source."
}

variable "repo_name" {
    type = string
    description = "Name of the repo that contains source."
}

variable "team" {
    type = string
    description = "Name of the team"
}

variable "targets" {
    type = list(string)
    description = "List of the target names that shall be deployed to in order of deployment stages"
}

variable "clusters" {
    type = map(object({
        cluster_id = string
        })
    )
    description = "Clusters that have been created and shall be used as targets. Keys must be a superset of targets list."
}

variable "repo_branch" {
    type = string
    description = "Name of the branch that should trigger CICD when pushed to."
}