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

# Create demo transactions in the ledger for the demo user accounts.
#
# Gerenated transactions follow a pattern of biweekly large deposits with
# periodic small payments to randomly choosen accounts.
#
# To run, set environment variable USE_DEMO_DATA="True"

set -u


# skip adding transactions if not enabled
if [ -z "$USE_DEMO_DATA" ] && [ "$USE_DEMO_DATA" != "True"  ]; then
    echo "\$USE_DEMO_DATA not \"True\"; no demo transactions added"
    exit 0
fi


# Expected environment variables for Spanner
readonly ENV_VARS=(
  "SPANNER_PROJECT_ID"
  "SPANNER_INSTANCE_ID"
  "SPANNER_DATABASE_ID"
  "LOCAL_ROUTING_NUM"
)


add_transaction() {
    TRANSACTION_ID=$7
    DATE=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" --date="@$(($6))")
    echo "adding demo transaction: $1 -> $2 (ID: $TRANSACTION_ID)"

    # Use gcloud spanner to insert row
    gcloud spanner rows insert \
        --project="$SPANNER_PROJECT_ID" \
        --instance="$SPANNER_INSTANCE_ID" \
        --database="$SPANNER_DATABASE_ID" \
        --table=TRANSACTIONS \
        --data=TRANSACTION_ID="$TRANSACTION_ID",FROM_ACCT="$1",TO_ACCT="$2",FROM_ROUTE="$3",TO_ROUTE="$4",AMOUNT="$5",TIMESTAMP="$DATE"
}


create_transactions() {
    PAY_PERIODS=3
    DAYS_BETWEEN_PAY=14
    SECONDS_IN_PAY_PERIOD=$(( 86400 * $DAYS_BETWEEN_PAY  ))
    DEPOSIT_AMOUNT=250000

    # create a UNIX timestamp in seconds since the Epoch
    START_TIMESTAMP=$(( $(date +%s) - $(( $(($PAY_PERIODS+1)) * $SECONDS_IN_PAY_PERIOD  ))  ))

    # Transaction ID counter (Spanner sequence will be used in application, but for demo data we use sequential IDs)
    TRANSACTION_ID=1

    for i in $(seq 1 $PAY_PERIODS); do
        # create deposit transaction for each user
        for account in ${USER_ACCOUNTS[@]}; do
            add_transaction "$EXTERNAL_ACCOUNT" "$account" "$EXTERNAL_ROUTING" "$LOCAL_ROUTING_NUM" $DEPOSIT_AMOUNT $START_TIMESTAMP $TRANSACTION_ID
            TRANSACTION_ID=$((TRANSACTION_ID + 1))
        done

        # create 15-20 payments between users
        TRANSACTIONS_PER_PERIOD=$(shuf -i 15-20 -n1)
        for p in $(seq 1 $TRANSACTIONS_PER_PERIOD); do
            # randomly generate an amount between $10-$100
            AMOUNT=$(shuf -i 1000-10000 -n1)

            # randomly select a sender and receiver
            SENDER_ACCOUNT=${USER_ACCOUNTS[$RANDOM % ${#USER_ACCOUNTS[@]}]}
            RECIPIENT_ACCOUNT=${USER_ACCOUNTS[$RANDOM % ${#USER_ACCOUNTS[@]}]}
            # if sender equals receiver, send to a random anonymous account
            if [[ "$SENDER_ACCOUNT" == "$RECIPIENT_ACCOUNT" ]]; then
                RECIPIENT_ACCOUNT=$(shuf -i 1000000000-9999999999 -n1)
            fi

            TIMESTAMP=$(( $START_TIMESTAMP + $(( $SECONDS_IN_PAY_PERIOD * $p / $(($TRANSACTIONS_PER_PERIOD + 1 )) )) ))

            add_transaction "$SENDER_ACCOUNT" "$RECIPIENT_ACCOUNT" "$LOCAL_ROUTING_NUM" "$LOCAL_ROUTING_NUM" $AMOUNT $TIMESTAMP $TRANSACTION_ID
            TRANSACTION_ID=$((TRANSACTION_ID + 1))
        done

        START_TIMESTAMP=$(( $START_TIMESTAMP + $(( $i * $SECONDS_IN_PAY_PERIOD  )) ))
    done
}


create_ledger() {
  # Account numbers for users 'testuser', 'alice', 'bob', and 'eve'.
  USER_ACCOUNTS=("1011226111" "1033623433" "1055757655" "1077441377")
  # Numbers for external account 'External Bank'
  EXTERNAL_ACCOUNT="9099791699"
  EXTERNAL_ROUTING="808889588"

  create_transactions
}


main() {
  # Check environment variables are set
	for env_var in ${ENV_VARS[@]}; do
    if [[ -z "${env_var}" ]]; then
      echo "Error: environment variable '$env_var' not set. Aborting."
      exit 1
    fi
  done

  create_ledger
}


main
