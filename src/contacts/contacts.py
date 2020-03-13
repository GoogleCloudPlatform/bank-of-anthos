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

"""Web service for handling linked user contacts.

Manages internal user contacts and external accounts.
"""

import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

import bleach
import jwt


APP = Flask(__name__)
APP.config["MONGO_URI"] = 'mongodb://{}/users'.format(
        os.environ.get('ACCOUNTS_DB_ADDR'))
MONGO = PyMongo(APP)

@APP.route('/version', methods=['GET'])
def version():
    """
    Service version endpoint
    """
    return os.environ.get('VERSION'), 200

@APP.route('/ready', methods=['GET'])
def ready():
    """Readiness probe."""
    return 'ok', 200


@APP.route('/contacts', methods=['GET'])
def get_contacts():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
        accountid = payload['acct']
        # contact data
        query = {'accountid': accountid}
        projection = {'contact_accts': True}
        result = MONGO.db.accounts.find_one(query, projection)

        acct_list = []
        if result is not None:
            acct_list = result['contact_accts']

        # (fixme): Remove DEFAULT_CONTACTS when frontend implemented to add contacts.
        acct_list = acct_list + DEFAULT_CONTACTS

        return jsonify({'account_list': acct_list}), 200
    except jwt.exceptions.InvalidTokenError as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 401

@APP.route('/contacts', methods=['POST'])
def get_add():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
        # TODO: validate contact information
        # add new contact to database
        contact = request.get_json()
        query = {'accountid': payload['acct']}
        update = {'$push': {'contact_accts': contact}}
        MONGO.db.accounts.update(query, update, upsert=True)
        return jsonify({}), 201
    except jwt.exceptions.InvalidTokenError as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 401
    except PyMongo.PyMongoError as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 500


if __name__ == '__main__':
    for v in ['PORT', 'ACCOUNTS_DB_ADDR', 'PUB_KEY_PATH', 'LOCAL_ROUTING_NUM']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            sys.exit(1)
    LOCAL_ROUTING = os.environ.get('LOCAL_ROUTING_NUM')

    DEFAULT_CONTACTS = [{'label': 'External Checking',
                        'account_num': '0123456789',
                        'routing_num': '111111111',
                        'deposit': True},
                        {'label': 'External Savings',
                        'account_num': '9876543210',
                        'routing_num': '222222222',
                        'deposit': True},
                        {'label': 'Friend',
                        'account_num': '1122334455',
                        'routing_num': LOCAL_ROUTING,
                        'deposit': False},
                        {'label': 'Mom',
                        'account_num': '6677889900',
                        'routing_num': LOCAL_ROUTING,
                        'deposit': False}]

    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
