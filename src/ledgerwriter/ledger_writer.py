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

import redis

from flask import Flask, jsonify, request

app = Flask(__name__)

ledger_host = os.getenv('LEDGER_ADDR')
ledger_port = os.getenv("LEDGER_PORT")
ledger_stream = os.getenv('LEDGER_STREAM')


@app.route('/new_transaction', methods=['POST'])
def add_transaction():
    # TODO: validate
    trans_obj = request.get_json()
    trans_obj['date'] = time.time()
    logging.info('adding transaction: %s' % str(trans_obj))
    _ledger.xadd(ledger_stream, trans_obj)
    return jsonify({}), 201


if __name__ == '__main__':
    for v in ['PORT', 'LEDGER_ADDR', 'LEDGER_STREAM', 'LEDGER_PORT']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    _ledger = redis.Redis(host=ledger_host, port=ledger_port, db=0)

    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
