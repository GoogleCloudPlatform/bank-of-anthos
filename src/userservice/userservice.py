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

import bcrypt
import bleach
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import uuid
import logging
import os
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://{}/users'.format(os.environ.get('USER_DB_ADDR'))
mongo = PyMongo(app)

@app.route('/create_user', methods=['POST'])
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
    logging.info('validating new user request: %s' % str(req))

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
    if any(field not in req for field in fields)
        return jsonify({'msg':'missing required field(s)'}), 400
    if any(not (value or value.strip()) for value in req.values()):
        return jsonify({'msg':'missing value for input field(s)'}), 400

    # check if user exists
    query = {'username':req['username']}
    if mongo.db.users.find_one(query) is not None:
        return jsonify({'msg':'user already exists'}), 400

    # check if passwords match
    if not req['password'] == req['password-repeat']:
        return jsonify({'msg':'passwords don\'t match'}), 400

    logging.info('creating user: %s' % str(req))
    # create password hash with salt
    password = req['password']
    salt = bcrypt.gensalt()
    passhash = bcrypt.hashpw(password.encode('utf-8'), salt)

    # insert user in MongoDB
    accountid = generate_accountid()
    data = {'username':req['username'],
            'accountid':accountid,
            'passhash':passhash,
            'firstname':req['firstname'],
            'lastname':req['lastname'],
            'birthday':req['birthday'],
            'timezone':req['timezone'],
            'address':req['address'],
            'state':req['state'],
            'zip':req['zip'],
            'ssn':req['ssn']}
    result = mongo.db.users.insert_one(data)

    if not result.acknowledged:
        return jsonify({'msg':'create user failed'}), 500
    return jsonify({}), 201


@app.route('/get_user', methods=['GET'])
def get_user():
    """Get a user record.

    Fails if there is no such user.
    
    request:
      - username

    response:
      - accountid
      - username
      - passhash
      - firstname
      - lastname
      - birthday
      - timezone
      - address
      - state
      - zip
      - ssn
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[-1]
    else:
        token = ''
    try:
        payload = jwt.decode(token, key=_public_key, algorithms='RS256')
        user = payload['user']
        logging.info('getting user: %s' % str(user))
        # get user from MongoDB
        query = {'username': user}
        fields = {'_id': False,
                  'passhash': False}
        result = mongo.db.users.find_one(query, fields)
        if result is None:
            return jsonify({'msg': 'user not found'}), 400
        return jsonify(result), 201
    except jwt.exceptions.InvalidTokenError as e:
        logging.error(e)
        return jsonify({'error': str(e)}), 401


@app.route('/login', methods=['GET'])
def get_token():
    username = bleach.clean(request.args.get('username'))
    password = bleach.clean(request.args.get('password'))

    # get user from MongoDB
    query = {'username': username}
    result = mongo.db.users.find_one(query)

    if result is not None:
        if bcrypt.checkpw(password.encode('utf-8'), result['passhash']):
            payload = {'user': username,
                       'acct': result['accountid'],
                       'name': '{} {}'.format(result['firstname'], result['lastname']),
                       'iat': datetime.utcnow(),
                       'exp': datetime.utcnow() + timedelta(seconds=_expiry_seconds)
                       }
            token = jwt.encode(payload, _private_key, algorithm='RS256')
            return jsonify({'token': token.decode("utf-8")}), 200
    return jsonify({'msg':'invalid login'}), 400


def generate_accountid():
    """Generates a globally unique alphanumerical accountid."""
    accountid = str(uuid.uuid4())
    while mongo.db.users.find_one({'accountid':accountid}) is not None:
        accountid = str(uuid.uuid4())
    return accountid


if __name__ == '__main__':
    for v in ['PORT', 'USER_DB_ADDR', 'TOKEN_EXPIRY_SECONDS', 'PRIV_KEY_PATH',
            'PUB_KEY_PATH']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    _expiry_seconds = int(os.environ.get('TOKEN_EXPIRY_SECONDS'))
    _private_key = open(os.environ.get('PRIV_KEY_PATH'), 'r').read()
    _public_key = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
