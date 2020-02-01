# Copyright 2019 Google LLC
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
"""
Balancereader keeps a read-only cache of the balances of each address
in the ledger
"""

import logging
import os
import sys
import threading
from collections import defaultdict

from flask import Flask, jsonify, request
import jwt
import redis


APP = Flask(__name__)


@APP.route('/ready', methods=['GET'])
def readiness():
    """
    Readiness probe
    """
    return 'ok', 200


@APP.route('/healthy', methods=['GET'])
def liveness():
    """
    Liveness probe. Fail if background thread dies
    """
    if BACKGROUND_THREAD is not None and BACKGROUND_THREAD.is_alive():
        return 'ok', 200
    return 'error', 500


@APP.route('/get_balance', methods=['GET'])
def get_balance():
    """
    Returns snapshot of user's balance

    Fails if token is not valid
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
        account_id = payload['acct']
        balance = BALANCE_DICT[account_id]
        return jsonify({'balance': balance}), 200
    except jwt.exceptions.InvalidTokenError as err:
        logging.error(err)
        return jsonify({'error': str(err)}), 401


def _process_transaction(transaction):
    """
    Process a new incoming transaction. Update cached account balances
    """
    sender_acct = transaction['fromAccountNum']
    sender_route = transaction['fromRoutingNum']
    receiver_acct = transaction['toAccountNum']
    receiver_route = transaction['toRoutingNum']
    amount = int(transaction['amount'])
    if sender_route == LOCAL_ROUTING:
        BALANCE_DICT[sender_acct] -= amount
    if receiver_route == LOCAL_ROUTING:
        BALANCE_DICT[receiver_acct] += amount


def _query_transactions(last_transaction_id=b'0-0', block=True):
    """
    Query ledger for new incoming transactions to process
    """
    if block:
        # block until new transactions arrive
        block_time = 0
    else:
        # don't block
        block_time = None

    new_set = LEDGER.xread({LEDGER_STREAM: last_transaction_id},
                           block=block_time)
    if len(new_set) > 0:
        for entry in new_set[0][1]:
            last_transaction_id = entry[0]
            transaction = entry[1]
            logging.info('processing transaction: %s', transaction)
            _process_transaction(transaction)
    return last_transaction_id


def transaction_listener(last_transaction_id):
    """
    Continuously query ledger for incoming transactions
    """
    while True:
        last_transaction_id = _query_transactions(
            last_transaction_id=last_transaction_id,
            block=True
        )


if __name__ == '__main__':
    for v in ['PORT', 'LEDGER_ADDR', 'LEDGER_STREAM', 'LEDGER_PORT',
              'LOCAL_ROUTING_NUM', 'PUB_KEY_PATH']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            sys.exit(1)

    # setup global variables
    BALANCE_DICT = defaultdict(int)
    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    LEDGER_STREAM = os.getenv('LEDGER_STREAM')
    LEDGER = redis.Redis(host=os.getenv("LEDGER_ADDR"),
                         port=os.getenv("LEDGER_PORT"), db=0)
    LOCAL_ROUTING = os.getenv('LOCAL_ROUTING_NUM')

    # build balance dictionary
    logging.info('restoring balances...')
    CACHE_RESTORE_POINT = _query_transactions(block=False)

    # start background transaction listener thread
    logging.info('starting transaction listener thread...')
    BACKGROUND_THREAD = threading.Thread(target=transaction_listener,
                                         args=[CACHE_RESTORE_POINT])
    BACKGROUND_THREAD.daemon = True
    BACKGROUND_THREAD.start()

    # start serving requests
    logging.info("starting flask...")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
