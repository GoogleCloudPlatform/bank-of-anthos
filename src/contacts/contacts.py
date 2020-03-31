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

import atexit
import logging
import os
import re
import sys

import bleach
from flask import Flask, jsonify, request
import jwt
from sqlalchemy import create_engine, MetaData, Table, Column, String, Boolean
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())

APP = Flask(__name__)


@APP.route('/version', methods=['GET'])
def version():
    """
    Service version endpoint
    """
    return VERSION, 200

@APP.route('/ready', methods=['GET'])
def ready():
    """Readiness probe."""
    return 'ok', 200


@APP.route('/contacts/<username>', methods=['POST'])
def add_contact(username):
    """Add a new favorite account to user's contacts list

    Fails if account or routing number are invalid
    or if label is not alphanumeric

    request fields:
    - account_num
    - routing_num
    - label
    - is_external
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
    except jwt.exceptions.InvalidTokenError as e:
        return jsonify({'msg': 'invalid authentication'}), 401
    if username != payload['user']:
        return jsonify({'msg': 'authorization denied'}), 401

    req = {k: bleach.clean(v) for k, v in request.get_json().items()}
    logging.debug('validating add contact request: %s', str(req))
    # Check if required fields are filled
    fields = ('label',
              'account_num',
              'routing_num')
    if any(f not in req for f in fields):
        return jsonify({'msg': 'missing required field(s)'}), 400
    if any(not bool(req[f] or req[f].strip()) for f in fields):
        return jsonify({'msg': 'missing value for input field(s)'}), 400

    # Don't allow self reference
    if (req['account_num'] == payload['acct'] and
            req['routing_num'] == LOCAL_ROUTING):
        return jsonify({'error': 'may not add yourself to contacts'}), 400
    # Validate account number (must be 10 digits)
    if (not re.match(r'\A[0-9]{10}\Z', req['account_num']) or
            req['account_num'] == payload['acct']):
        return jsonify({'msg': 'invalid account number'}), 400
    # Validate routing number (must be 9 digits)
    if not re.match(r'\A[0-9]{9}\Z', req['routing_num']):
        return jsonify({'msg': 'invalid routing number'}), 400
    # Only allow external accounts to deposit
    if req['is_external'] and req['routing_num'] == LOCAL_ROUTING:
        return jsonify({'msg': 'invalid routing number'}), 400
    # Validate label (must be <40 chars, only alphanumeric and spaces)
    if (not all(s.isalnum() for s in req['label'].split()) or
            len(req['label']) > 40):
        return jsonify({'msg': 'invalid account label'}), 400

    try:
        _add_contact(username, req)
    except SQLAlchemyError as e:
        logging.error(e)
        return jsonify({'error': 'failed to add contact'}), 500

    return jsonify({}), 201


@APP.route('/contacts/<username>', methods=['GET'])
def get_contacts(username):
    """Retrieve the contacts list for the authenticated user.
    This list is used for populating Payment and Deposit fields.

    Return: a list of contacts
            {'account_list': [account1, account2, ...]}
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256')
    except jwt.exceptions.InvalidTokenError as e:
        return jsonify({'msg': 'invalid authentication'}), 401
    if username != payload['user']:
        return jsonify({'msg': 'authorization denied'}), 401

    try:
        contacts_list = _get_contacts(username)
    except SQLAlchemyError as e:
        logging.error(e)
        return jsonify({'error': 'failed to retrieve contacts list'}), 500

    return jsonify({'account_list': contacts_list}), 200


def _add_contact(username, contact):
    """Add a contact under the specified username.

    Params: username - the username of the user
            contact - a key/value dict of contact attributes
                      {'label': label, 'account_num': account_num, ...}
    Raises: SQLAlchemyError if there was an issue with the database
    """
    data = {'username': username,
            'label': contact['label'],
            'account_num': contact['account_num'],
            'routing_num': contact['routing_num'],
            'is_external': contact['is_external']}
    logging.debug('QUERY: %s', str(statement))
    statement = CONTACTS_TABLE.insert().values(data)
    DB_CONN.execute(statement)


def _get_contacts(username):
    """Get a list of contacts for the specified username.

    Params: username - the username of the user
    Return: a list of contacts in the form of key/value attribute dicts,
            [ {'label': contact1, ...}, {'label': contact2, ...}, ...]
    Raises: SQLAlchemyError if there was an issue with the database
    """
    contacts = list()
    statement = CONTACTS_TABLE.select().where(
            CONTACTS_TABLE.c.username == username)
    logging.debug('QUERY: %s', str(statement))
    result = DB_CONN.execute(statement)
    logging.debug('RESULT: %s', str(result))
    for row in result:
        contact = {
                'label': row['label'],
                'account_num': row['account_num'],
                'routing_num': row['routing_num'],
                'is_external': row['is_external']}
        contacts.append(contact)

    return contacts


@atexit.register
def _shutdown():
    """Executed when web app is terminated."""
    DB_CONN.close()
    logging.info("Stopping flask.")
    logging.shutdown()


if __name__ == '__main__':
    env_vars = ['PORT',
                'VERSION',
                'PUB_KEY_PATH',
                'ACCOUNTS_DB_ADDR',
                'ACCOUNTS_DB_PORT',
                'ACCOUNTS_DB_USER',
                'ACCOUNTS_DB_PASS',
                'ACCOUNTS_DB_NAME']
    for v in env_vars:
        if os.environ.get(v) is None:
            logging.error("error: environment variable %s not set", v)
            logging.shutdown()
            sys.exit(1)

    VERSION = os.environ.get('VERSION')
    LOCAL_ROUTING = os.environ.get('LOCAL_ROUTING_NUM')
    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()

    # Configure database connection
    _accounts_db = create_engine(
            'postgresql://{user}:{password}@{host}:{port}/{database}'.format(
                user=os.environ.get('ACCOUNTS_DB_USER'),
                password=os.environ.get('ACCOUNTS_DB_PASS'),
                host=os.environ.get('ACCOUNTS_DB_ADDR'),
                port=os.environ.get('ACCOUNTS_DB_PORT'),
                database=os.environ.get('ACCOUNTS_DB_NAME')))
    CONTACTS_TABLE = Table('contacts', MetaData(_accounts_db),
            Column('username', String),
            Column('label', String),
            Column('account_num', String),
            Column('routing_num', String),
            Column('is_external', Boolean))
    DB_CONN = _accounts_db.connect()

    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
