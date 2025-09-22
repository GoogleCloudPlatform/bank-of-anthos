#!/bin/bash

# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
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
  echo "no demo queue data added"
  exit 0
fi

# Expected environment variables
readonly ENV_VARS=(
  "POSTGRES_DB"
  "POSTGRES_USER"
)

add_investment_entry() {
  # Usage: add_investment_entry "ACCOUNT" "TIER1" "TIER2" "TIER3" "UUID" "STATUS"
  echo "adding investment queue entry: $5 (Account: $1)"
  psql -X -v ON_ERROR_STOP=1 -v account="$1" -v tier1="$2" -v tier2="$3" -v tier3="$4" -v uuid="$5" -v status="$6" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
    VALUES (:'account', :'tier1', :'tier2', :'tier3', :'uuid', :'status') 
    ON CONFLICT (uuid) DO NOTHING;
EOSQL
}

add_withdrawal_entry() {
  # Usage: add_withdrawal_entry "ACCOUNT" "TIER1" "TIER2" "TIER3" "UUID" "STATUS"
  echo "adding withdrawal queue entry: $5 (Account: $1)"
  psql -X -v ON_ERROR_STOP=1 -v account="$1" -v tier1="$2" -v tier2="$3" -v tier3="$4" -v uuid="$5" -v status="$6" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
    VALUES (:'account', :'tier1', :'tier2', :'tier3', :'uuid', :'status') 
    ON CONFLICT (uuid) DO NOTHING;
EOSQL
}

# Load test data into the database
create_queue_entries() {
  # Sample investment requests (positive amounts)
  add_investment_entry "1011226111" "1000.00" "2000.00" "500.00" "550e8400-e29b-41d4-a716-446655440001" "PENDING"
  add_investment_entry "1011226112" "500.00" "1500.00" "1000.00" "550e8400-e29b-41d4-a716-446655440002" "PENDING"
  add_investment_entry "1011226113" "2000.00" "0.00" "3000.00" "550e8400-e29b-41d4-a716-446655440003" "PROCESSING"
  
  # Sample withdrawal requests (positive amounts for withdrawal queue)
  add_withdrawal_entry "1011226114" "500.00" "1000.00" "0.00" "550e8400-e29b-41d4-a716-446655440004" "PENDING"
  add_withdrawal_entry "1011226115" "0.00" "2000.00" "500.00" "550e8400-e29b-41d4-a716-446655440005" "PENDING"
  
  # Sample completed requests
  add_investment_entry "1011226116" "1500.00" "2500.00" "1000.00" "550e8400-e29b-41d4-a716-446655440006" "COMPLETED"
  add_withdrawal_entry "1011226117" "1000.00" "0.00" "2000.00" "550e8400-e29b-41d4-a716-446655440007" "COMPLETED"
  
  # Sample failed requests
  add_investment_entry "1011226118" "5000.00" "10000.00" "15000.00" "550e8400-e29b-41d4-a716-446655440008" "FAILED"
  add_withdrawal_entry "1011226119" "3000.00" "5000.00" "2000.00" "550e8400-e29b-41d4-a716-446655440009" "CANCELLED"
  
  # Sample mixed tier requests
  add_investment_entry "1011226120" "0.00" "3000.00" "0.00" "550e8400-e29b-41d4-a716-446655440010" "PENDING"
  add_investment_entry "1011226121" "2500.00" "0.00" "0.00" "550e8400-e29b-41d4-a716-446655440011" "PENDING"
  add_investment_entry "1011226122" "0.00" "0.00" "4000.00" "550e8400-e29b-41d4-a716-446655440012" "PENDING"
  
  # Additional withdrawal requests
  add_withdrawal_entry "1011226123" "1000.00" "0.00" "0.00" "550e8400-e29b-41d4-a716-446655440013" "PENDING"
  add_withdrawal_entry "1011226124" "0.00" "1500.00" "0.00" "550e8400-e29b-41d4-a716-446655440014" "PENDING"
  add_withdrawal_entry "1011226125" "0.00" "0.00" "2000.00" "550e8400-e29b-41d4-a716-446655440015" "PENDING"
}

main() {
  # Check environment variables are set
  for env_var in ${ENV_VARS[@]}; do
    if [[ -z "${!env_var}" ]]; then
      echo "Error: environment variable '$env_var' not set. Aborting."
      exit 1
    fi
  done

  create_queue_entries
}

main
