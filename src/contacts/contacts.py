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

DEFAULT_EXT_ACCTS = [{'label': 'External Checking',
                      'account_number': '0123456789',
                      'routing_number': '111111111'},
                     {'label': 'External Savings',
                      'account_number': '9876543210',
                      'routing_number': '222222222'}]

DEFAULT_CONTACTS = [{'label': 'Friend',
                     'account_number': '1122334455'},
                    {'label': 'Mom',
                     'account_number': '6677889900'}]

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


@APP.route('/accounts/external', methods=['GET', 'POST'])
def external_accounts():
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
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
        accountid = payload['acct']

        if request.method == 'GET':
            return _get_ext_accts(accountid)

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
    result = MONGO.db.accounts.find_one(query, projection)

    acct_list = []
    if result is not None:
        acct_list = result['ext_accounts']

    # (fixme): Remove DEFAULT_EXT_ACCTS when frontend implemented to add external accounts.
    acct_list = acct_list + DEFAULT_EXT_ACCTS

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
    result = MONGO.db.accounts.update(query, update, params)

    if not result.acknowledged:
        return jsonify({'error': 'add external account failed'}), 500
    return jsonify({}), 201


@APP.route('/accounts/contacts', methods=['GET', 'POST'])
def contacts():
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
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
        accountid = payload['acct']

        if request.method == 'GET':
            return _get_contacts(accountid)

        if request.method == 'POST':
            req = {k: bleach.clean(v) for k, v in request.form.items()}
            # check if required fields are present
            fields = ('label',
                      'account_number')
            if any(field not in req for field in fields):
                return jsonify({'error': 'missing required field(s)'}), 400

            contact = {'label': req['label'],
                       'account_number': req['account_number']}

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
    result = MONGO.db.contacts.find_one(query, projection)

    acct_list = []
    if result is not None:
        acct_list = result['contact_accts']

    # (fixme): Remove DEFAULT_CONTACTS when frontend implemented to add contacts.
    acct_list = acct_list + DEFAULT_CONTACTS

    # Add the banking routing number for this banking application
    for contact in acct_list:
        contact['routing_number'] = LOCAL_ROUTING
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
    if MONGO.db.users.find_one(query) is None:
        return jsonify({'error': 'contact account number does not exist'}), 400

    # add the contact
    query = {'accountid': accountid}
    update = {'$push': {'contact_accts': contact}}
    params = {'upsert': True}
    result = MONGO.db.accounts.update(query, update, params)

    if not result.acknowledged:
        return jsonify({'error': 'add contact failed'}), 500
    return jsonify({}), 201


if __name__ == '__main__':
    for v in ['PORT', 'ACCOUNTS_DB_ADDR', 'PUB_KEY_PATH', 'LOCAL_ROUTING_NUM']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            sys.exit(1)
    LOCAL_ROUTING = os.environ.get('LOCAL_ROUTING_NUM')
    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
