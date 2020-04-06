#!/bin/sh
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


# create default transactions in the ledger for the default user account.
# to make the history look realistic, we use biweekly large deposits,
# followed by periodic small payments to random accounts.
# values are chosen so that the depsoit in a period > payments in the same period
set -u

# skip adding transactions if not enabled
if [ "$USE_DEFAULT_DATA" != "True"  ]; then
    echo "no default transactions added"
    exit 0
fi

add_transaction() {
    DATE=$(date -u +"%Y-%m-%d %H:%M:%S.%3N%z" --date="@$(($6))")
    echo "adding default transaction: $1 -> $2"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        INSERT INTO TRANSACTIONS (FROM_ACCT, TO_ACCT, FROM_ROUTE, TO_ROUTE, AMOUNT, TIMESTAMP)
        VALUES ($1, $2, $3, $4, $5, '$DATE');
EOSQL
}

PAY_PREIODS=3
DAYS_BETWEEN_PAY=14
SECONDS_IN_PAY_PERIOD=$(( 86400 * $DAYS_BETWEEN_PAY  ))
echo $SECONDS_IN_PAY_PERIOD
DEPOSIT_AMOUNT=250000

START_TIMESTAMP=$(( $(date +%s) - $(( $(($PAY_PREIODS+1)) * $SECONDS_IN_PAY_PERIOD  ))  ))
for i in $(seq 1 $PAY_PREIODS); do
    # create deposit transaction
    add_transaction $DEFAULT_DEPOSIT_ACCOUNT $DEFAULT_ACCOUNT $DEFAULT_DEPOSIT_ROUTING $LOCAL_ROUTING_NUM $DEPOSIT_AMOUNT $START_TIMESTAMP
    # create payments
    TRANSACTIONS_PER_PERIOD=$(shuf -i 3-11 -n1)
    for p in $(seq 1 $TRANSACTIONS_PER_PERIOD); do
        AMOUNT=$(shuf -i 100-25000 -n1)
        ACCOUNT=$(shuf -i 1000000000-9999999999 -n1)
        TIMESTAMP=$(( $START_TIMESTAMP + $(( $SECONDS_IN_PAY_PERIOD * $p / $(($TRANSACTIONS_PER_PERIOD + 1 )) )) ))
        add_transaction $DEFAULT_ACCOUNT $ACCOUNT $LOCAL_ROUTING_NUM $LOCAL_ROUTING_NUM $AMOUNT $TIMESTAMP
    done
    START_TIMESTAMP=$(( $START_TIMESTAMP + $(( $i * $SECONDS_IN_PAY_PERIOD  )) ))
done

