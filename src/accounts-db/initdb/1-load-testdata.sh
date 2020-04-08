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

# Skip adding data if not enabled
if [ "$USE_DEFAULT_DATA" != "True"  ]; then
    echo "no default users added"
    exit 0
fi


# Expected environment variables
readonly ENV_VARS=(
  "POSTGRES_DB"
  "POSTGRES_USER"
  "LOCAL_ROUTING_NUM"
  "DEFAULT_USER_ACCOUNT"
  "DEFAULT_USER_USERNAME"
)


# Load test data into the database
load_testdata() {
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" $POSTGRES_DB <<-EOSQL
		INSERT INTO users VALUES ('$DEFAULT_USER_ACCOUNT', '$DEFAULT_USER_USERNAME', '\x243262243132245273764737474f39777562452f4a786a79444a7263756f386568466b762e634e5262356e6867746b474752584c6634437969346643', '$DEFAULT_USER_NAME', 'Testuser', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$DEFAULT_USER_USERNAME', '$DEFAULT_DEPOSIT_LABEL', '$DEFAULT_DEPOSIT_ACCOUNT', '$DEFAULT_DEPOSIT_ROUTING', 'true') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$DEFAULT_USER_USERNAME', '$DEFAULT_CONTACT1_LABEL', '$DEFAULT_CONTACT1_ACCOUNT', '$LOCAL_ROUTING_NUM', 'false') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$DEFAULT_USER_USERNAME', '$DEFAULT_CONTACT2_LABEL', '$DEFAULT_CONTACT2_ACCOUNT', '$LOCAL_ROUTING_NUM', 'false') ON CONFLICT DO NOTHING;

		INSERT INTO users VALUES ('$DEFAULT_CONTACT1_ACCOUNT', '$DEFAULT_CONTACT1_LABEL', '\x243262243132245273764737474f39777562452f4a786a79444a7263756f386568466b762e634e5262356e6867746b474752584c6634437969346643', '$DEFAULT_CONTACT1_LABEL', 'Testuser', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$DEFAULT_CONTACT1_LABEL', '$DEFAULT_DEPOSIT_LABEL', '$DEFAULT_DEPOSIT_ACCOUNT', '$DEFAULT_DEPOSIT_ROUTING', 'true') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$DEFAULT_CONTACT1_LABEL', '$DEFAULT_USER_NAME', '$DEFAULT_USER_ACCOUNT', '$LOCAL_ROUTING_NUM', 'false') ON CONFLICT DO NOTHING;

		INSERT INTO users VALUES ('$DEFAULT_CONTACT2_ACCOUNT', '$DEFAULT_CONTACT2_LABEL', '\x243262243132245273764737474f39777562452f4a786a79444a7263756f386568466b762e634e5262356e6867746b474752584c6634437969346643', '$DEFAULT_CONTACT2_LABEL', 'Testuser', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$DEFAULT_CONTACT2_LABEL', '$DEFAULT_DEPOSIT_LABEL', '$DEFAULT_DEPOSIT_ACCOUNT', '$DEFAULT_DEPOSIT_ROUTING', 'true') ON CONFLICT DO NOTHING;
		INSERT INTO contacts VALUES ('$DEFAULT_CONTACT2_LABEL', '$DEFAULT_USER_NAME', '$DEFAULT_USER_ACCOUNT', '$LOCAL_ROUTING_NUM', 'false') ON CONFLICT DO NOTHING;
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
