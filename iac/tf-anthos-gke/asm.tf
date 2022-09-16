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

module "asm" {
  source                    = "terraform-google-modules/kubernetes-engine/google//modules/asm"
  version                   = "~> 23.0"
  project_id                = data.google_project.project.project_id
  cluster_name              = module.gke.name
  cluster_location          = module.gke.location
  enable_cni                = true
  enable_fleet_registration = false
  enable_mesh_feature       = true
}

module "istio-annotation" {
  source = "terraform-google-modules/gcloud/google//modules/kubectl-wrapper"

  project_id              = data.google_project.project.project_id
  cluster_name            = module.gke.name
  cluster_location        = module.gke.location
  module_depends_on       = [module.gke]
  kubectl_create_command  = "kubectl annotate --overwrite namespace default mesh.cloud.google.com/proxy='{\"managed\":\"true\"}'"
  kubectl_destroy_command = "kubectl annotate --overwrite namespace default mesh.cloud.google.com/proxy='{\"managed\":\"false\"}'"
}


module "istio-injection-label" {
  source = "terraform-google-modules/gcloud/google//modules/kubectl-wrapper"

  project_id              = data.google_project.project.project_id
  cluster_name            = module.gke.name
  cluster_location        = module.gke.location
  module_depends_on       = [module.gke]
  kubectl_create_command  = "kubectl label namespace default istio-injection=enabled istio.io/rev- --overwrite"
  kubectl_destroy_command = "kubectl label namespace default istio-injection-"
}