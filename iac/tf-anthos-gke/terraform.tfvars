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

region       = "us-central1"
zone         = "us-central1-b"
cluster_name = "anthos-sample-cluster1"
sync_repo    = "https://github.com/GoogleCloudPlatform/bank-of-anthos"
sync_branch  = "v0.5.9"
sync_rev     = ""
policy_dir   = "/kubernetes-manifests"