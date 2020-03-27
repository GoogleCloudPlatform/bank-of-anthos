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
Userservice manages user account creation, user login, and related tasks
"""

import atexit
from datetime import datetime, timedelta
import logging
import os
import random
import sys

import bleach
import bcrypt
from flask import Flask, jsonify, request
import jwt
from sqlalchemy import create_engine, Metadata, Table, Column, String, Date
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
def readiness():
    """
    Readiness probe
    """
    return 'ok', 200


@APP.route('/users', methods=['POST'])
def create_user():
    """Create a user record.

    Fails if that username already exists.

    Generates a unique accountid.

    request:
      - username
      - password
      - password-repeat
      - firstname
      - lastname
      - birthday
      - timezone
      - address
      - state
      - zip
      - ssn
    """
    req = {k: bleach.clean(v) for k, v in request.form.items()}
    logging.debug('validating create user request: %s', str(req))

    # Check if required fields are filled
    fields = ('username',
              'password',
              'password-repeat',
              'firstname',
              'lastname',
              'birthday',
              'timezone',
              'address',
              'state',
              'zip',
              'ssn')
    if any(f not in req for f in fields):
        return jsonify({'msg': 'missing required field(s)'}), 400
    if any(not bool(req[f] or req[f].strip()) for f in fields):
        return jsonify({'msg': 'missing value for input field(s)'}), 400

    # Check if passwords match
    if not req['password'] == req['password-repeat']:
        return jsonify({'msg': 'passwords do not match'}), 400

    try:
        # Check if user exists
        statement = USERS_TABLE.select().where(
                USERS_TABLE.c.username == req['username']).as_scalar()
        logging.debug('QUERY: %s', str(statement))
        result = DB_CONN.execute(statement).first()
        logging.debug('RESULT: %s', str(result))
        if result is not None:
            return jsonify({'msg': 'user already exists'}), 400
        logging.debug('creating user: %s', str(req))

        # Create password hash with salt
        password = req['password']
        salt = bcrypt.gensalt()
        passhash = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Add user to database
        accountid = _generate_accountid()
        data = {'accountid': accountid,
                'username': req['username'],
                'passhash': passhash,
                'firstname': req['firstname'],
                'lastname': req['lastname'],
                'birthday': req['birthday'],
                'timezone': req['timezone'],
                'address': req['address'],
                'state': req['state'],
                'zip': req['zip'],
                'ssn': req['ssn']}
        statement = USERS_TABLE.insert().values(data)
        logging.debug('QUERY: %s', str(statement))
        DB_CONN.execute(statement)

        return jsonify({}), 201
    except SQLAlchemyError as e:
        logging.error(e)
        return jsonify({'error': 'create user failed'}), 500


@APP.route('/login', methods=['GET'])
def get_token():
    """Login a user and return a JWT token

    Fails if username doesn't exist or password doesn't match hash

    token expiry time determined by environment variable

    request:
      - username
      - password
    """
    username = bleach.clean(request.args.get('username'))
    password = bleach.clean(request.args.get('password'))

    try:
        # Get user data
        statement = USERS_TABLE.select().where(
                USERS_TABLE.c.username == username)
        logging.debug('QUERY: %s', str(statement))
        result = dict(DB_CONN.execute(statement).first())
        logging.debug('RESULT: %s', str(result))

        # Validate the password
        if not bcrypt.checkpw(password.encode('utf-8'), result['passhash']):
            return jsonify({'msg': 'invalid login'}), 400

        full_name = '{} {}'.format(result['firstname'], result['lastname'])
        exp_time = datetime.utcnow() + timedelta(seconds=EXPIRY_SECONDS)
        payload = {'user': username,
                   'acct': result['accountid'],
                   'name': full_name,
                   'iat': datetime.utcnow(),
                   'exp': exp_time}
        token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
        return jsonify({'token': token.decode("utf-8")}), 200
    except SQLAlchemyError as e:
        logging.error(e)
        return jsonify({'error': 'failed to retrieve user information'}), 500


def _generate_accountid():
    """Generates a globally unique alphanumerical accountid."""
    accountid = None
    while accountid is None:
        accountid = str(random.randint(1e9, (1e10-1)))

        statement = USERS_TABLE.select().where(
                USERS_TABLE.c.accountid == accountid)
        logging.debug('QUERY: %s', str(statement))
        result = DB_CONN.execute(statement).first()
        logging.debug('RESULT: %s', str(result))
        if result is None:
            accountid = None
    return accountid


@atexit.register
def _shutdown():
    """Executed when web app is terminated."""
    DB_CONN.close()
    logging.info("Stopping flask.")
    logging.shutdown()


if __name__ == '__main__':
    env_vars = ['PORT',
                'VERSION',
                'TOKEN_EXPIRY_SECONDS',
                'PRIV_KEY_PATH',
                'PUB_KEY_PATH',
                'ACCOUNTS_DB_ADDR',
                'ACCOUNTS_DB_PORT',
                'ACCOUNTS_DB_USER',
                'ACCOUNTS_DB_PASS',
                'ACCOUNTS_DB_NAME']
    for v in env_vars:
        if os.environ.get(v) is None:
            logging.critical("error: environment variable %s not set", v)
            logging.shutdown()
            sys.exit(1)

    VERSION = os.environ.get('VERSION')
    EXPIRY_SECONDS = int(os.environ.get('TOKEN_EXPIRY_SECONDS'))
    PRIVATE_KEY = open(os.environ.get('PRIV_KEY_PATH'), 'r').read()
    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()

    # Configure database connection
    _accounts_db = create_engine(
            'postgresql://{user}:{password}@{host}:{port}/{database}'.format(
                user=os.environ.get('ACCOUNTS_DB_USER'),
                password=os.environ.get('ACCOUNTS_DB_PASS'),
                host=os.environ.get('ACCOUNTS_DB_ADDR'),
                port=os.environ.get('ACCOUNTS_DB_PORT'),
                database=os.environ.get('ACCOUNTS_DB_NAME')))
    USERS_TABLE = Table('users', Metadata(_accounts_db),
            Column('accountid', String),
            Column('username', String),
            Column('passhash', String),
            Column('firstname', String),
            Column('lastname', String),
            Column('birthday', Date),
            Column('timezone', String),
            Column('address', String),
            Column('state', String),
            Column('zip', String),
            Column('ssn', String))
    DB_CONN = _accounts_db.connect()

    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
