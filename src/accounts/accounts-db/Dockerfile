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
FROM postgres:16.4-alpine@sha256:5660c2cbfea50c7a9127d17dc4e48543eedd3d7a41a595a2dfa572471e37e64c

# Files for initializing the database.
COPY initdb/0-accounts-schema.sql initdb/1-load-testdata.sh /docker-entrypoint-initdb.d/
RUN chmod 755 /docker-entrypoint-initdb.d/0-accounts-schema.sql /docker-entrypoint-initdb.d/1-load-testdata.sh 
