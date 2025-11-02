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

# Initialize Google Cloud Spanner database for Bank of Anthos ledger
#
# This script:
# 1. Creates a Spanner instance (if it doesn't exist)
# 2. Creates a database
# 3. Applies the DDL schema
# 4. Optionally loads demo data

set -e

# Expected environment variables
readonly ENV_VARS=(
  "SPANNER_PROJECT_ID"
  "SPANNER_INSTANCE_ID"
  "SPANNER_DATABASE_ID"
)

echo "Initializing Spanner database for Bank of Anthos ledger..."

# Check environment variables are set
for env_var in ${ENV_VARS[@]}; do
  if [[ -z "${!env_var}" ]]; then
    echo "Error: environment variable '$env_var' not set. Aborting."
    exit 1
  fi
done

# Set configuration
INSTANCE_CONFIG="${SPANNER_INSTANCE_CONFIG:-regional-us-central1}"
INSTANCE_NODES="${SPANNER_INSTANCE_NODES:-1}"

echo "Configuration:"
echo "  Project ID: $SPANNER_PROJECT_ID"
echo "  Instance ID: $SPANNER_INSTANCE_ID"
echo "  Database ID: $SPANNER_DATABASE_ID"
echo "  Instance Config: $INSTANCE_CONFIG"
echo "  Instance Nodes: $INSTANCE_NODES"

# Check if instance exists, create if it doesn't
echo "Checking if Spanner instance exists..."
if gcloud spanner instances describe "$SPANNER_INSTANCE_ID" --project="$SPANNER_PROJECT_ID" &>/dev/null; then
  echo "Instance '$SPANNER_INSTANCE_ID' already exists."
else
  echo "Creating Spanner instance '$SPANNER_INSTANCE_ID'..."
  gcloud spanner instances create "$SPANNER_INSTANCE_ID" \
    --project="$SPANNER_PROJECT_ID" \
    --config="$INSTANCE_CONFIG" \
    --nodes="$INSTANCE_NODES" \
    --description="Bank of Anthos Ledger Database Instance"
  echo "Instance created successfully."
fi

# Check if database exists, create if it doesn't
echo "Checking if database exists..."
if gcloud spanner databases describe "$SPANNER_DATABASE_ID" \
  --instance="$SPANNER_INSTANCE_ID" \
  --project="$SPANNER_PROJECT_ID" &>/dev/null; then
  echo "Database '$SPANNER_DATABASE_ID' already exists."
else
  echo "Creating database '$SPANNER_DATABASE_ID'..."
  gcloud spanner databases create "$SPANNER_DATABASE_ID" \
    --instance="$SPANNER_INSTANCE_ID" \
    --project="$SPANNER_PROJECT_ID"
  echo "Database created successfully."
fi

# Apply DDL schema
echo "Applying DDL schema from 0_init_tables.sql..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DDL_FILE="$SCRIPT_DIR/0_init_tables.sql"

if [[ ! -f "$DDL_FILE" ]]; then
  echo "Error: DDL file not found at $DDL_FILE"
  exit 1
fi

# Execute DDL statements
gcloud spanner databases ddl update "$SPANNER_DATABASE_ID" \
  --instance="$SPANNER_INSTANCE_ID" \
  --project="$SPANNER_PROJECT_ID" \
  --ddl-file="$DDL_FILE"

echo "DDL schema applied successfully."

# Load demo data if requested
if [[ "$USE_DEMO_DATA" == "True" ]]; then
  echo "Loading demo data..."
  bash "$SCRIPT_DIR/1_create_transactions.sh"
  echo "Demo data loaded successfully."
else
  echo "Skipping demo data load (USE_DEMO_DATA not set to 'True')."
fi

echo "Spanner database initialization complete!"
