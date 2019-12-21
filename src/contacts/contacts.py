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

from flask import Flask, jsonify, request

import jwt

app = Flask(__name__)


@app.route('/ready', methods=['GET'])
def add_contact():
    return 'ok', 200


@app.route('/external', methods=['GET', 'POST'])
def get_contact():
    if request.method == 'POST':
        logging.info('adding contacts not implemented')
        return jsonify({}), 501

    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        jwt.decode(token, key=_public_key, algorithms='RS256')
        # TODO: implement database. Hardcode for now
        acct_list = [{'label': 'External Checking',
                      'account_number': '0123456789',
                      'routing_number': '111111111'},
                     {'label': 'External Savings',
                      'account_number': '9876543210',
                      'routing_number': '222222222'}]
        return jsonify({'account_list': acct_list}), 200
    except jwt.exceptions.InvalidTokenError as e:
        logging.error(e)
        return jsonify({'error': str(e)}), 401


@app.route('/contacts', methods=['GET', 'POST'])
def get_external():
    if request.method == 'POST':
        logging.info('adding contacts not implemented')
        return jsonify({}), 501

    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        jwt.decode(token, key=_public_key, algorithms='RS256')
        # TODO: implement database. Hardcode for now
        acct_list = [{'label': 'Friend',
                      'account_number': '1122334455',
                      'routing_number': _local_routing},
                     {'label': 'Mom',
                      'account_number': '6677889900',
                      'routing_number': _local_routing}]
        return jsonify({'account_list': acct_list}), 200
    except jwt.exceptions.InvalidTokenError as e:
        logging.error(e)
        return jsonify({'error': str(e)}), 401


if __name__ == '__main__':
    for v in ['PORT', 'PUB_KEY_PATH', 'LOCAL_ROUTING_NUM']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    _local_routing = os.environ.get('LOCAL_ROUTING_NUM')
    _public_key = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
