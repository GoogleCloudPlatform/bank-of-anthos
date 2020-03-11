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

import logging
import os
import random
import sys
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import bleach
import bcrypt
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
    logging.info('validating new user request: %s', str(req))

    # check if required fields are filled
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
    if any(field not in req for field in fields):
        return jsonify({'msg': 'missing required field(s)'}), 400
    if any(not bool(req[field] or req[field].strip()) for field in fields):
        return jsonify({'msg': 'missing value for input field(s)'}), 400

    # check if user exists
    query = {'username': req['username']}
    if MONGO.db.users.find_one(query) is not None:
        return jsonify({'msg': 'user already exists'}), 400

    # check if passwords match
    if not req['password'] == req['password-repeat']:
        return jsonify({'msg': 'passwords don\'t match'}), 400

    logging.info('creating user: %s', str(req))
    # create password hash with salt
    password = req['password']
    salt = bcrypt.gensalt()
    passhash = bcrypt.hashpw(password.encode('utf-8'), salt)

    # insert user in MongoDB
    accountid = generate_accountid()
    data = {'username': req['username'],
            'accountid': accountid,
            'passhash': passhash,
            'firstname': req['firstname'],
            'lastname': req['lastname'],
            'birthday': req['birthday'],
            'timezone': req['timezone'],
            'address': req['address'],
            'state': req['state'],
            'zip': req['zip'],
            'ssn': req['ssn']}
    result = MONGO.db.users.insert_one(data)

    if not result.acknowledged:
        return jsonify({'msg': 'create user failed'}), 500
    return jsonify({}), 201


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

    # get user from MongoDB
    query = {'username': username}
    result = MONGO.db.users.find_one(query)

    if result is not None:
        if bcrypt.checkpw(password.encode('utf-8'), result['passhash']):
            full_name = '{} {}'.format(result['firstname'], result['lastname'])
            exp_time = datetime.utcnow() + timedelta(seconds=EXPIRY_SECONDS)
            payload = {'user': username,
                       'acct': result['accountid'],
                       'name': full_name,
                       'iat': datetime.utcnow(),
                       'exp': exp_time
                       }
            token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
            return jsonify({'token': token.decode("utf-8")}), 200
    return jsonify({'msg': 'invalid login'}), 400


def generate_accountid():
    """Generates a globally unique alphanumerical accountid."""
    accountid = None
    while (accountid is None or
           MONGO.db.users.find_one({'accountid': accountid}) is not None):
        accountid = str(random.randint(1e9, (1e10-1)))
    return accountid


if __name__ == '__main__':
    for v in ['PORT', 'ACCOUNTS_DB_ADDR', 'TOKEN_EXPIRY_SECONDS', 'PRIV_KEY_PATH',
              'PUB_KEY_PATH']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            sys.exit(1)
    EXPIRY_SECONDS = int(os.environ.get('TOKEN_EXPIRY_SECONDS'))
    PRIVATE_KEY = open(os.environ.get('PRIV_KEY_PATH'), 'r').read()
    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
