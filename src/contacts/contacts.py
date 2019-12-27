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

import bleach
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import jwt


app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://{}/users'.format(
        os.environ.get('ACCOUNTS_DB_ADDR'))
mongo = PyMongo(app)


@app.route('/ready', methods=['GET'])
def ready():
    """Readiness probe."""
    return 'ok', 200


@app.route('/external', methods=['GET', 'POST'])
def external():
    """Add or retrieve linked external accounts for the currently authorized user.

    External accounts are accounts for external banking institutions.

    Authorized requests only:  headers['Authorization'].

    GET: Get a list of linked external accounts for this user.
        Args: None
        Returns: a list of linked external accounts
            {'account_list': [account1, account2, ...]}

    POST: Adds a linked external account for this user.
        Args: HTTP form data
          - label
          - account_number
          - routing_number
        Returns: None
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=_public_key, algorithms='RS256')
        accountid = payload['acct']

        if request.method == 'GET':
            # (fixme): implement frontend to add accounts. Hardcode existing accounts for now
            # return _get_ext_accounts(accountid)
            acct_list = [{'label': 'External Checking',
                          'account_number': '0123456789',
                          'routing_number': '111111111'},
                         {'label': 'External Savings',
                          'account_number': '9876543210',
                          'routing_number': '222222222'}]
            return jsonify({'account_list': acct_list}), 200

        if request.method == 'POST':
            req = {k: bleach.clean(v) for k, v in request.form.items()}
            # check if required fields are present
            fields = ('label',
                      'account_number',
                      'routing_number')
            if any(field not in req for field in fields):
                return jsonify({'error': 'missing required field(s)'}), 400

            ext_acct = {'label': req['label'],
                        'account_number': req['account_number'],
                        'routing_number': req['routing_number']}
            return _add_ext_acct(accountid, ext_acct)

        msg = 'unsupported request method {}'.format(request.method)
        logging.info(msg)
        return jsonify({'error': msg}), 501

    except jwt.exceptions.InvalidTokenError as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 401


def _get_ext_accts(accountid):
    """Get a list of linked extenal accounts.

    Args:
        accountid: the user to get external accounts for

    Returns:
        A list of accounts:
        {'account_list': [account1, account2, ...]}

        Each account contains the following:
        {'label': ..., 'account_number': ..., 'routing_number': ...}
    """
    query = {'accountid': accountid}
    projection = {'external_accts': True}
    result = mongo.db.accounts.find_one(query, projection)

    acct_list = []
    if result is not None:
        acct_list = result['ext_accounts']
    return jsonify({'account_list': acct_list}), 200


def _add_ext_acct(accountid, ext_acct):
    """Add a linked external account.

    Args:
        accountid: the user to add this external account for
        ext_acct: the external account to add
            {'label': ..., 'account_number': ..., 'routing_number': ...}
    """
    query = {'accountid': accountid}
    update = {'$push': {'external_accts': ext_acct}}
    params = {'upsert': True}
    result = mongo.db.accounts.update(query, update, params)

    if not result.acknowledged:
        return jsonify({'error': 'add external account failed'}), 500
    return jsonify({}), 201


@app.route('/contacts', methods=['GET', 'POST'])
def get_contacts():
    """Add or retrieve linked contacts for the currently authorized user.

    Contacts are other users of this banking application.

    Authorized requests only:  headers['Authorization'].

    GET: Get a list of linked contact accounts for this user.
        Args: None
        Returns: a list of contact accounts
            {'account_list': [contact1, contact2, ...]}

    POST: Adds a linked contact account for this user.
        Args: HTTP form data
          - label
          - account_number
        Returns: None
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=_public_key, algorithms='RS256')
        accountid = payload['acct']

        if request.method == 'GET':
            # (fixme): implement frontend to add contacts. Hardcode existing contacts for now
            # return _get_contacts(accountid)
            acct_list = [{'label': 'Friend',
                          'account_number': '1122334455',
                          'routing_number': _local_routing},
                         {'label': 'Mom',
                          'account_number': '6677889900',
                          'routing_number': _local_routing}]
            return jsonify({'account_list': acct_list}), 200

        if request.method == 'POST':
            req = {k: bleach.clean(v) for k, v in request.form.items()}
            # check if required fields are present
            fields = ('label',
                      'account_number')
            if any(field not in req for field in fields):
                return jsonify({'error': 'missing required field(s)'}), 400

            contact = {'label': req['label'],
                       'account_number': req['account_number'],
                       'routing_number': _local_routing}

            return _add_contact(accountid, contact)

        msg = 'unsupported request method {}'.format(request.method)
        logging.info(msg)
        return jsonify({'error': msg}), 501

    except jwt.exceptions.InvalidTokenError as ex:
        logging.error(ex)
        return jsonify({'error': str(ex)}), 401


def _get_contacts(accountid):
    """Get a list of linked contacts.

    Args:
        accountid: the user to get contacts for

    Returns:
        A list of contacts:
        {'account_list': [contact1, contact2, ...]}

        Each contact contains the following:
        {'label': ..., 'account_number': ..., 'routing_number': ...}
    """
    query = {'accountid': accountid}
    projection = {'contact_accts': True}
    result = mongo.db.contacts.find_one(query, projection)

    acct_list = []
    if result is not None:
        acct_list = result['contact_accts']
    return jsonify({'account_list': acct_list}), 200


def _add_contact(accountid, contact):
    """Add a linked contact.

    Args:
        accountid: the user to add this contact for
        contact: the contact to add
            {'label': ..., 'account_number': ..., 'routing_number': ...}
    """
    # check if the contact account number exists
    query = {'accountid': contact['account_number']}
    if mongo.db.users.find_one(query) is None:
        return jsonify({'error': 'contact account number does not exist'}), 400

    # add the contact
    query = {'accountid': accountid}
    update = {'$push': {'contact_accts': contact}}
    params = {'upsert': True}
    result = mongo.db.accounts.update(query, update, params)

    if not result.acknowledged:
        return jsonify({'error': 'add contact failed'}), 500
    return jsonify({}), 201


if __name__ == '__main__':
    for v in ['PORT', 'ACCOUNTS_DB_ADDR', 'PUB_KEY_PATH', 'LOCAL_ROUTING_NUM']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            sys.exit(1)
    _local_routing = os.environ.get('LOCAL_ROUTING_NUM')
    _public_key = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
