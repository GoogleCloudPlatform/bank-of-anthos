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

FROM postgres:16.13-alpine@sha256:20edbde7749f822887a1a022ad526fde0a47d6b2be9a8364433605cf65099416

# Need to get coreutils to get the date bash function working properly:
RUN apk add --no-cache coreutils && rm -rf /var/cache/apk/*

# Files for initializing the database.
COPY initdb/0_init_tables.sql initdb/1_create_transactions.sh /docker-entrypoint-initdb.d/
RUN chmod 755  /docker-entrypoint-initdb.d/0_init_tables.sql /docker-entrypoint-initdb.d/1_create_transactions.sh

# Run as the postgres user (Issue #517)
USER 999