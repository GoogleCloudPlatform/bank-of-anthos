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

from flask import Flask, jsonify, request
import bleach
import bcrypt
import jwt
from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, LargeBinary
from sqlalchemy.exc import OperationalError, SQLAlchemyError

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

    request fields:
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
    try:
        req = {k: bleach.clean(v) for k, v in request.form.items()}
        _validate_new_user(req)

        # Check if user already exists
        if _get_user(req['username']) is not None:
            raise NameError('user {} already exists'.format(req['username']))

        # Create the user
        _add_user(req)

    except UserWarning as warn:
        return jsonify({'msg': str(warn)}), 400
    except NameError as err:
        return jsonify({'msg': str(err)}), 409
    except SQLAlchemyError as err:
        logging.error(err)
        return jsonify({'error': 'failed to create user'}), 500

    return jsonify({}), 201


def _validate_new_user(req):
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
        raise UserWarning('missing required field(s)')
    if any(not bool(req[f] or req[f].strip()) for f in fields):
        raise UserWarning('missing value for input field(s)')

    # Check if passwords match
    if not req['password'] == req['password-repeat']:
        raise UserWarning('passwords do not match')


@APP.route('/login', methods=['GET'])
def get_token():
    """Login a user and return a JWT token

    Fails if username doesn't exist or password doesn't match hash

    token expiry time determined by environment variable

    request fields:
      - username
      - password
    """
    username = bleach.clean(request.args.get('username'))
    password = bleach.clean(request.args.get('password'))

    # Get user data
    try:
        user = _get_user(username)
        if user is None:
            raise LookupError('user {} does not exist'.format(user))

        # Validate the password
        if not bcrypt.checkpw(password.encode('utf-8'), user['passhash']):
            raise PermissionError('invalid login')

        full_name = '{} {}'.format(user['firstname'], user['lastname'])
        exp_time = datetime.utcnow() + timedelta(seconds=EXPIRY_SECONDS)
        payload = {'user': username,
                   'acct': user['accountid'],
                   'name': full_name,
                   'iat': datetime.utcnow(),
                   'exp': exp_time}
        token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
        return jsonify({'token': token.decode("utf-8")}), 200

    except LookupError as err:
        return jsonify({'msg': str(err)}), 404
    except PermissionError as err:
        return jsonify({'msg': str(err)}), 401
    except SQLAlchemyError as err:
        logging.error(err)
        return jsonify({'error': 'failed to retrieve user information'}), 500


def _add_user(user):
    """Add a user to the database.

    Params: user - a key/value dict of attributes describing a new user
                   {'username': username, 'password': password, ...}
    Raises: SQLAlchemyError if there was an issue with the database
    """
    # Create password hash with salt
    password = user['password']
    salt = bcrypt.gensalt()
    passhash = bcrypt.hashpw(password.encode('utf-8'), salt)

    accountid = _generate_accountid()

    # Add user to database
    data = {'accountid': accountid,
            'username': user['username'],
            'passhash': passhash,
            'firstname': user['firstname'],
            'lastname': user['lastname'],
            'birthday': user['birthday'],
            'timezone': user['timezone'],
            'address': user['address'],
            'state': user['state'],
            'zip': user['zip'],
            'ssn': user['ssn']}
    statement = USERS_TABLE.insert().values(data)
    logging.debug('QUERY: %s', str(statement))
    DB_CONN.execute(statement)


def _get_user(username):
    """Get user data for the specified username.

    Params: username - the username of the user
    Return: a key/value dict of user attributes,
            {'username': username, 'accountid': accountid, ...}
            or None if that user does not exist
    Raises: SQLAlchemyError if there was an issue with the database
    """
    statement = USERS_TABLE.select().where(
        USERS_TABLE.c.username == username)
    logging.debug('QUERY: %s', str(statement))
    result = DB_CONN.execute(statement).first()
    logging.debug('RESULT: %s', str(result))

    return dict(result) if result is not None else None


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
        # If there already exists an account, try again.
        if result is not None:
            accountid = None
    return accountid


@atexit.register
def _shutdown():
    """Executed when web app is terminated."""
    try:
        DB_CONN.close()
    except NameError:
        # catch name error when DB_CONN not set up
        pass
    logging.info("Stopping flask.")
    logging.shutdown()


if __name__ == '__main__':
    for v in ['PORT',
              'VERSION',
              'PRIV_KEY_PATH',
              'PUB_KEY_PATH',
              'TOKEN_EXPIRY_SECONDS',
              'ACCOUNTS_DB_URI']:
        if os.environ.get(v) is None:
            logging.critical("error: environment variable %s not set", v)
            logging.shutdown()
            sys.exit(1)

    VERSION = os.environ.get('VERSION')
    EXPIRY_SECONDS = int(os.environ.get('TOKEN_EXPIRY_SECONDS'))
    PRIVATE_KEY = open(os.environ.get('PRIV_KEY_PATH'), 'r').read()
    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()

    # Configure database connection
    try:
        ACCOUNTS_DB = create_engine(os.environ.get('ACCOUNTS_DB_URI'))
        USERS_TABLE = Table('users', MetaData(ACCOUNTS_DB),
                            Column('accountid', String),
                            Column('username', String),
                            Column('passhash', LargeBinary),
                            Column('firstname', String),
                            Column('lastname', String),
                            Column('birthday', Date),
                            Column('timezone', String),
                            Column('address', String),
                            Column('state', String),
                            Column('zip', String),
                            Column('ssn', String))
        DB_CONN = ACCOUNTS_DB.connect()
    except OperationalError:
        logging.critical("database connection failed")
        sys.exit(1)

    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
