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

import redis

import requests


app = Flask(__name__)

ledger_host = os.getenv('LEDGER_ADDR')
ledger_port = os.getenv("LEDGER_PORT")
ledger_stream = os.getenv('LEDGER_STREAM')

_local_routing_num = os.getenv('LOCAL_ROUTING_NUM')
_balance_service_uri = 'http://{}/get_balance'.format(
    os.environ.get('BALANCES_API_ADDR'))


@app.route('/new_transaction', methods=['POST'])
def add_transaction():
    transaction = request.get_json()
    sender_acct = transaction['from_account_num']
    sender_route = transaction['from_routing_num']
    recv_route = transaction['to_routing_num']
    amount = int(transaction['amount'])

    # ensure sender or reciever belongs to this bank
    if sender_route != _local_routing_num and recv_route != _local_routing_num:
        return 'expected routing number not found', 500
    # ensure amount is proper value
    if amount <= 0:
        return 'invalid transaction amount', 500
    # ensure sender balance can cover transaction
    if sender_route == _local_routing_num:
        req = requests.get(url=_balance_service_uri,
                           params={'account_id': sender_acct})
        resp = req.json()
        sender_balance = resp['balance']
        if sender_balance < amount:
            return 'insufficient balance', 500

    transaction['date'] = time.time()
    logging.info('adding transaction: %s' % str(transaction))
    _ledger.xadd(ledger_stream, transaction)
    return jsonify({}), 201


if __name__ == '__main__':
    for v in ['PORT', 'LEDGER_ADDR', 'LEDGER_STREAM', 'LEDGER_PORT',
            'LOCAL_ROUTING_NUM', 'BALANCES_API_ADDR']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    _ledger = redis.Redis(host=ledger_host, port=ledger_port, db=0)

    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
