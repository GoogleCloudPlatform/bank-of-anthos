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

import logging
import os
import time

from flask import Flask, jsonify, request

import jwt

import redis

import requests


app = Flask(__name__)


_balance_service_uri = 'http://{}/get_balance'.format(
    os.environ.get('BALANCES_API_ADDR'))


@app.route('/new_transaction', methods=['POST'])
def add_transaction():
    """
    Adds a new transaction to the internal ledger

    Fails if:
    - token is not valid
    - token does not belong to the sender (unless external deposit)
    - amount is <= 0
    - sender doesn't have sufficient balance
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=_public_key, algorithms='RS256')
        transaction = request.get_json()
        send_acct = transaction['from_account_num']
        send_route = transaction['from_routing_num']
        amount = int(transaction['amount'])

        initiator_acct = payload['acct']

        # ensure sender is the one who initiated this transaction
        # TODO: check if external account belongs to initiator if doing deposit
        if not ((send_acct == initiator_acct and send_route == _local_routing)
                or (send_route != _local_routing)):
            return jsonify({'error': 'not authorized'}), 401
        # ensure amount is proper value
        if amount <= 0:
            return jsonify({'error': 'invalid transaction amount'}), 50
        # ensure sender balance can cover transaction
        if send_route == _local_routing:
            hed = {'Authorization': 'Bearer ' + token}
            req = requests.get(url=_balance_service_uri, headers=hed)
            resp = req.json()
            sender_balance = resp['balance']
            if sender_balance < amount:
                return jsonify({'error': 'insufficient balance'}), 50
        # transaction looks valid
        transaction['date'] = time.time()
        logging.info('adding transaction: %s' % str(transaction))
        _ledger.xadd(_ledger_stream, transaction)
        return jsonify({}), 201
    except jwt.exceptions.InvalidTokenError as e:
        logging.error(e)
        return jsonify({'error': str(e)}), 401


if __name__ == '__main__':
    for v in ['PORT', 'LEDGER_ADDR', 'LEDGER_STREAM', 'LEDGER_PORT',
              'LOCAL_ROUTING_NUM', 'BALANCES_API_ADDR', 'PUB_KEY_PATH']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    _public_key = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    _ledger_stream = os.getenv('LEDGER_STREAM')
    _ledger = redis.Redis(host=os.getenv("LEDGER_ADDR"),
                          port=os.getenv("LEDGER_PORT"), db=0)
    _local_routing = os.getenv('LOCAL_ROUTING_NUM')

    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
