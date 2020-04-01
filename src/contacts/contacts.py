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
import re
import sys

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from pymongo.errors import PyMongoError

import jwt


logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())

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


@APP.route('/contacts/<username>', methods=['GET'])
def get_contacts(username):
    """Retrieve the contacts list for the authenticated user.
    This list is used for populating Payment and Deposit fields.

    Returns: a list of contacts
            {'account_list': [account1, account2, ...]}
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
        if username != payload['user']:
            raise PermissionError('not authorized')
        # get data
        query = {'user': username}
        projection = {'contact_accts': True}
        result = MONGO.db.accounts.find_one(query, projection)
        acct_list = []
        if result is not None:
            acct_list = result['contact_accts']
        return jsonify({'account_list': acct_list}), 200
    except (jwt.exceptions.InvalidTokenError, PermissionError) as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 401

@APP.route('/contacts/<username>', methods=['POST'])
def add_contact(username):
    """Add a new favorite account to user's contacts list

    Fails if account or routing number are invalid
    or if label is not alphanumeric

    request:
    - account_num
    - routing_num
    - label
    """

    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
        if username != payload['user']:
            raise PermissionError('not authorized')
        contact = request.get_json()
        # don't allow self reference
        if (contact['account_num'] == payload['acct'] and
                contact['routing_num'] == LOCAL_ROUTING):
            raise RuntimeError('can\'t add self to contacts')
        # validate account number (must be 10 digits)
        if (not re.match(r'\A[0-9]{10}\Z', contact['account_num']) or
                contact['account_num'] == payload['acct']):
            raise RuntimeError('invalid account number')
        # validate routing number (must be 9 digits)
        if not re.match(r'\A[0-9]{9}\Z', contact['routing_num']):
            raise RuntimeError('invalid routing number')
        # only allow external accounts to deposit
        if contact['is_external'] and contact['routing_num'] == LOCAL_ROUTING:
            raise RuntimeError('invalid routing number')
        # validate label (must be <40 chars, only alphanumeric and spaces)
        if (not all(s.isalnum() for s in contact['label'].split()) or
                len(contact['label']) > 40):
            raise RuntimeError('invalid account label')
        # add new contact to database
        query = {'user': username}
        update = {'$push': {'contact_accts': contact}}
        MONGO.db.accounts.update(query, update, upsert=True)
        return jsonify({}), 201
    except (jwt.exceptions.InvalidTokenError, PermissionError) as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 401
    except (PyMongoError, RuntimeError) as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 500


if __name__ == '__main__':
    for v in ['PORT', 'ACCOUNTS_DB_ADDR', 'PUB_KEY_PATH', 'LOCAL_ROUTING_NUM']:
        if os.environ.get(v) is None:
            logging.error("error: environment variable %s not set", v)
            logging.shutdown()
            sys.exit(1)
    LOCAL_ROUTING = os.environ.get('LOCAL_ROUTING_NUM')

    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
