#!/bin/bash
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

# Immediately exit if any error occurs during script execution.
set -o errexit


# Expected environment variables
readonly ENV_VARS=(
  "POSTGRES_DB"
  "POSTGRES_USER"
  "LOCAL_ROUTING_NUM"
  "TEST_ACCOUNTID"
  "TEST_USERNAME"
)


# Load test data into the database
load_testdata() {
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" $POSTGRES_DB <<-EOSQL
		INSERT INTO users VALUES ('$TEST_ACCOUNTID', '$TEST_USERNAME', '\x243262243132245273764737474f39777562452f4a786a79444a7263756f386568466b762e634e5262356e6867746b474752584c6634437969346643', 'Test', 'User', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333') ON CONFLICT DO NOTHING;

		INSERT INTO contacts VALUES ('$TEST_USERNAME', 'External Checking', '9999999999', '987654321', 'true') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$TEST_USERNAME', 'External Savings', '8888888888', '987654321', 'true') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$TEST_USERNAME', 'Alice', '2222222222', '$LOCAL_ROUTING_NUM', 'false') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$TEST_USERNAME', 'Bob', '3333333333', '$LOCAL_ROUTING_NUM', 'false') ON CONFLICT DO NOTHING;
EOSQL
}


main() {
  # Check environment variables are set
	for env_var in ${ENV_VARS[@]}; do
    if [[ -z "${!env_var}" ]]; then
      echo "Error: environment variable '$env_var' not set. Aborting."
      exit 1
    fi
  done

	load_testdata
}


main
