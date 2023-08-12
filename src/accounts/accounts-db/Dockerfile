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
FROM postgres:15.4-alpine@sha256:f36c528a2dc8747ea40b4cb8578da69fa75c5063fd6a71dcea3e3b2a6404ff7b

# Files for initializing the database.
COPY initdb/0-accounts-schema.sql /docker-entrypoint-initdb.d/0-accounts-schema.sql
RUN chmod 755  /docker-entrypoint-initdb.d/0-accounts-schema.sql
COPY initdb/1-load-testdata.sh /docker-entrypoint-initdb.d/1-load-testdata.sh
RUN chmod 755  /docker-entrypoint-initdb.d/1-load-testdata.sh
