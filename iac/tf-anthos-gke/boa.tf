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

module "boa-secret" {
  source = "terraform-google-modules/gcloud/google//modules/kubectl-wrapper"

  project_id              = data.google_project.project.project_id
  cluster_name            = module.gke.name
  cluster_location        = module.gke.location
  module_depends_on       = [module.gke]
  kubectl_create_command  = "kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/bank-of-anthos/${var.sync_branch}/extras/jwt/jwt-secret.yaml"
  kubectl_destroy_command = "kubectl delete -f https://raw.githubusercontent.com/GoogleCloudPlatform/bank-of-anthos/${var.sync_branch}/extras/jwt/jwt-secret.yaml"
}

module "boa-istio" {
  source = "terraform-google-modules/gcloud/google//modules/kubectl-wrapper"

  project_id        = data.google_project.project.project_id
  cluster_name      = module.gke.name
  cluster_location  = module.gke.location
  module_depends_on = [module.asm.wait]

  kubectl_create_command  = "kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/bank-of-anthos/${var.sync_branch}/istio-manifests/frontend-ingress.yaml"
  kubectl_destroy_command = "kubectl delete -f https://raw.githubusercontent.com/GoogleCloudPlatform/bank-of-anthos/${var.sync_branch}/istio-manifests/frontend-ingress.yaml"
}