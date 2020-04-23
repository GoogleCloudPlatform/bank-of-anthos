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


add_user() {
	psql -X -v ON_ERROR_STOP=1 -v account="$1" -v username="$2" -v firstname="$3" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
		INSERT INTO users VALUES (:'account', :'username', '\x243262243132245273764737474f39777562452f4a786a79444a7263756f386568466b762e634e5262356e6867746b474752584c6634437969346643', :'firstname', 'Testuser', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333') ON CONFLICT DO NOTHING;
EOSQL
}


add_external_account() {
	psql -X -v ON_ERROR_STOP=1 -v username="$1" -v label="$2" -v account="$3" -v routing="$4" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
		INSERT INTO contacts VALUES (:'username', :'label', :'account', :'routing', 'true') ON CONFLICT DO NOTHING;
EOSQL
}


add_contact() {
	psql -X -v ON_ERROR_STOP=1 -v username="$1" -v label="$2" -v account="$3" -v routing="$LOCAL_ROUTING_NUM" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
		INSERT INTO contacts VALUES (:'username', :'label', :'account', :'routing', 'false') ON CONFLICT DO NOTHING;
EOSQL
}


# Load test data into the database
load_testdata() {
  # Add the default user with an external deposit account and contacts A & B
  add_user "$DEFAULT_USER_ACCOUNT" "$DEFAULT_USER_USERNAME" "$DEFAULT_USER_NAME"
  add_external_account "$DEFAULT_USER_USERNAME" "$DEFAULT_DEPOSIT_LABEL" "$DEFAULT_DEPOSIT_ACCOUNT" "$DEFAULT_DEPOSIT_ROUTING"
  add_contact "$DEFAULT_USER_USERNAME" "$DEFAULT_CONTACT_NAME_A" "$DEFAULT_CONTACT_ACCOUNT_A"
  add_contact "$DEFAULT_USER_USERNAME" "$DEFAULT_CONTACT_NAME_B" "$DEFAULT_CONTACT_ACCOUNT_B"

  # Add contact A as a user with the default user as a contact
  add_user "$DEFAULT_CONTACT_ACCOUNT_A" "$DEFAULT_CONTACT_NAME_A" "$DEFAULT_CONTACT_NAME_A"
  add_external_account "$DEFAULT_CONTACT_NAME_A" "$DEFAULT_DEPOSIT_LABEL" "$DEFAULT_DEPOSIT_ACCOUNT" "$DEFAULT_DEPOSIT_ROUTING"
  add_contact "$DEFAULT_CONTACT_NAME_A" "$DEFAULT_USER_NAME" "$DEFAULT_USER_ACCOUNT"

  # Add contact B as a user with the default user as a contact
  add_user "$DEFAULT_CONTACT_ACCOUNT_B" "$DEFAULT_CONTACT_NAME_B" "$DEFAULT_CONTACT_NAME_B"
  add_external_account "$DEFAULT_CONTACT_NAME_B" "$DEFAULT_DEPOSIT_LABEL" "$DEFAULT_DEPOSIT_ACCOUNT" "$DEFAULT_DEPOSIT_ROUTING"
  add_contact "$DEFAULT_CONTACT_NAME_B" "$DEFAULT_USER_NAME" "$DEFAULT_USER_ACCOUNT"
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
