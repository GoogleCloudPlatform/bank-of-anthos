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
  echo "no demo assets added"
  exit 0
fi

# Expected environment variables
readonly ENV_VARS=(
  "POSTGRES_DB"
  "POSTGRES_USER"
)

add_asset() {
  # Usage: add_asset "TIER" "NAME" "AMOUNT" "PRICE"
  echo "adding asset: $2 (Tier $1)"
  psql -X -v ON_ERROR_STOP=1 -v tier="$1" -v name="$2" -v amount="$3" -v price="$4" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
    VALUES (:'tier', :'name', :'amount', :'price') 
    ON CONFLICT (asset_name) DO NOTHING;
EOSQL
}

# Load test data into the database
create_assets() {
  # Tier 1: Most liquid assets (Cryptocurrencies)
  add_asset "1" "BTC" "150.50000000" "45000.00"
  add_asset "1" "ETH" "2500.75000000" "3000.00"
  add_asset "1" "USDT" "1000000.00000000" "1.00"
  add_asset "1" "USDC" "1000000.00000000" "1.00"
  add_asset "1" "XRP" "500000.00000000" "0.50"

  # Tier 2: Medium liquidity (36-48 hrs settlement)
  add_asset "2" "SP500_ETF" "10000.00000000" "450.75"
  add_asset "2" "NASDAQ_ETF" "15000.00000000" "375.50"
  add_asset "2" "AAPL" "25000.00000000" "175.25"
  add_asset "2" "MSFT" "20000.00000000" "325.50"
  add_asset "2" "BOND_FUND" "50000.00000000" "100.00"

  # Tier 3: Less liquid investments
  add_asset "3" "REAL_ESTATE_FUND" "5000.00000000" "1000.00"
  add_asset "3" "PRIVATE_EQUITY_A" "2500.00000000" "5000.00"
  add_asset "3" "VENTURE_FUND_X" "1000.00000000" "10000.00"
  add_asset "3" "HEDGE_FUND_Y" "750.00000000" "15000.00"
  add_asset "3" "INFRASTRUCTURE_Z" "1500.00000000" "2500.00"
}

main() {
  # Check environment variables are set
  for env_var in ${ENV_VARS[@]}; do
    if [[ -z "${!env_var}" ]]; then
      echo "Error: environment variable '$env_var' not set. Aborting."
      exit 1
    fi
  done

  create_assets
}

main
