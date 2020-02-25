# Copyright 2020 Google LLC
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

# This script backs up the running accounts-db so we can start with some initial content

#!/bin/sh
POD=$(kubectl get pod -l app=accounts-db -o jsonpath="{.items[0].metadata.name}")
echo $POD
kubectl cp $POD:data ./data
rm -rf ./data/db/configdb
rm -rf ./data/db/*.lock
rm -rf ./data/db/journal
rm -rf ./data/db/diagnostic.data
