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
if [ "$USE_DEMO_DATA" != "True"  ]; then
  echo "no demo users added"
  exit 0
fi

# Expected environment variables
readonly ENV_VARS=(
  "POSTGRES_DB"
  "POSTGRES_USER"
  "LOCAL_ROUTING_NUM"
)

# Function to add users with separate salt and passhash fields
add_user() {
  # Usage: add_user "ACCOUNTID" "USERNAME" "FIRST_NAME"
  echo "adding user: $2"
  
  # Split the DEFAULT_PASSHASH into salt and passhash
  IFS='|' read -r salt passhash <<< "$DEFAULT_PASSHASH"
  
  # Insert user data into the database
  psql -X -v ON_ERROR_STOP=1 \
    -v account="$1" \
    -v username="$2" \
    -v firstname="$3" \
    -v passhash="\\x$passhash" \
    -v salt="\\x$salt" \
    --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO users (accountid, username, passhash, salt, firstname, lastname, birthday, timezone, address, state, zip, ssn)
    VALUES (:'account', :'username', :'passhash', :'salt', :'firstname', 'User', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333') 
    ON CONFLICT DO NOTHING;
EOSQL
}

add_external_account() {
  # Usage:  add_external_account "OWNER_USERNAME" "LABEL" "ACCOUNT" "ROUTING"
  echo "user $1 adding contact: $2"
  psql -X -v ON_ERROR_STOP=1 -v username="$1" -v label="$2" -v account="$3" -v routing="$4" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO contacts VALUES (:'username', :'label', :'account', :'routing', 'true') ON CONFLICT DO NOTHING;
EOSQL
}

add_contact() {
  # Usage:  add_contact "OWNER_USERNAME" "CONTACT_LABEL" "CONTACT_ACCOUNT"
  echo "user $1 adding external account: $2"
  psql -X -v ON_ERROR_STOP=1 -v username="$1" -v label="$2" -v account="$3" -v routing="$LOCAL_ROUTING_NUM" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO contacts VALUES (:'username', :'label', :'account', :'routing', 'false') ON CONFLICT DO NOTHING;
EOSQL
}

# Load test data into the database
create_accounts() {
  # Add demo users.
  add_user "1011226111" "testuser" "Test"
  add_user "1033623433" "alice" "Alice"
  add_user "1055757655" "bob" "Bob"
  add_user "1077441377" "eve" "Eve"

  # Make everyone contacts of each other
  add_contact "testuser" "Alice" "1033623433"
  add_contact "testuser" "Bob" "1055757655"
  add_contact "testuser" "Eve" "1077441377"
  add_contact "alice" "Testuser" "1011226111"
  add_contact "alice" "Bob" "1055757655"
  add_contact "alice" "Eve" "1077441377"
  add_contact "bob" "Testuser" "1011226111"
  add_contact "bob" "Alice" "1033623433"
  add_contact "bob" "Eve" "1077441377"
  add_contact "eve" "Testuser" "1011226111"
  add_contact "eve" "Alice" "1033623433"
  add_contact "eve" "Bob" "1055757655"

  # Add external accounts
  add_external_account "testuser" "External Bank" "9099791699" "808889588"
  add_external_account "alice" "External Bank" "9099791699" "808889588"
  add_external_account "bob" "External Bank" "9099791699" "808889588"
  add_external_account "eve" "External Bank" "9099791699" "808889588"
}

main() {
  # Check environment variables are set
  for env_var in ${ENV_VARS[@]}; do
    if [[ -z "${!env_var}" ]]; then
      echo "Error: environment variable '$env_var' not set. Aborting."
      exit 1
    fi
  done

  # A password hash + salt for the demo password 'bankofsplunk'
  #DEFAULT_PASSHASH='47e6106bff23748cad32f10911a094e8|b4d9e941eaf9e1a9b5b5c4f57d22ddb8123b8a47467e52685dd4f06b4152398d'
  DEFAULT_PASSHASH='0e0ab7fc8ad0f68d8c0a88da06a7e79e|5da0a1304c22bec69bdb74f66d590cd4a0d585063ecbd7d1120662ddf55c49c8'  
  create_accounts
}

main