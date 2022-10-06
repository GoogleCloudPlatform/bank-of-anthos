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

set -Eeuo pipefail

echo '🚀  Starting ./03-wait-for-asm.sh'
echo '🕰  Waiting for GKE cluster setup to complete provisioning managed Service Mesh with managed Control Plane and managed Data Plane.'
echo '🍵 🧉 🫖  This will possibly take dozens of minutes - why not get ANOTHER hot beverage?  🍵 🧉 🫖'
while true
do 
    output=$( gcloud container fleet mesh describe | grep "      state: " | grep -v ACTIVE ) || output=""
    if ! [ -n "$output" ]
    then
        break
    else
        sleep 15
        echo -ne "."
    fi
done
echo '✅  Finished ./03-wait-for-asm.sh'
