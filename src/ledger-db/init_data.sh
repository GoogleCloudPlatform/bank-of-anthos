#!/bin/sh

# create default transactions in the ledger for the default user account.
# to make the history look realistic, we use biweekly large deposits,
# followed by periodic small payments to random accounts.
# values are chosen so that the depsoit in a period > payments in the same period

DEFAULT_ACCOUNT=7673361018
LOCAL_ROUTING_NUM=123456789
DEPOSIT_ACCOUNT=9999999999
DEPOSIT_ROUTING=000000000

PAY_PREIODS=3
DAYS_BETWEEN_PAY=14
let SECONDS_IN_PAY_PERIOD=60*60*24*$DAYS_BETWEEN_PAY
DEPOSIT_AMOUNT=250000

START_TIMESTAMP=$(( $(date +%s) - $(( $(($PAY_PREIODS+1)) * $SECONDS_IN_PAY_PERIOD  ))  ))
for i in $(seq 1 $PAY_PREIODS); do
    # create deposit transaction
    echo XADD ledger \* fromAccountNum $DEPOSIT_ACCOUNT fromRoutingNum $DEPOSIT_ROUTING toAccountNum $DEFAULT_ACCOUNT toRoutingNum $LOCAL_ROUTING_NUM amount $DEPOSIT_AMOUNT timestamp $START_TIMESTAMP
    # create payments
    TRANSACTIONS_PER_PERIOD=$((  $RANDOM % 8 + 3 ))
    for p in $(seq 1 $TRANSACTIONS_PER_PERIOD); do
        AMOUNT=$(( (RANDOM % 25000) + 100 ))
        ACCOUNT=$(($RANDOM%9+1))$(($RANDOM%9+1))$(($RANDOM%9+1))$(($RANDOM%9+1))$(($RANDOM%9+1))$(($RANDOM%9+1))$(($RANDOM%9+1))$(($RANDOM%9+1))$(($RANDOM%9+1))
        TIMESTAMP=$(( $START_TIMESTAMP + $(( $SECONDS_IN_PAY_PERIOD * $p / $(($TRANSACTIONS_PER_PERIOD + 1 )) )) ))
        echo XADD ledger \* fromAccountNum $DEFAULT_ACCOUNT fromRoutingNum $LOCAL_ROUTING_NUM toAccountNum $ACCOUNT toRoutingNum $LOCAL_ROUTING_NUM amount $AMOUNT timestamp $TIMESTAMP
    done
    START_TIMESTAMP=$(( $START_TIMESTAMP + $(( $i * $SECONDS_IN_PAY_PERIOD  )) ))
done

