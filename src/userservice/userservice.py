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
    print(req)
    logging.info('creating user: %s' % str(req))

    # check if user exists
    query = {'username':req['username']}
    if mongo.db.users.find_one(query) is not None:
        return jsonify({'msg':'user already exists'}), 400

    # create password hash with salt
    password = req['password']
    salt = bcrypt.gensalt()
    passhash = bcrypt.hashpw(password.encode(), salt)

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
      - salt
      - hash
      - firstname
      - lastname
      - birthday
      - timezone
      - address
      - state
      - zip
      - ssn
    """
    req = {k: bleach.clean(v) for k, v in request.get_json().items()}
    logging.info('getting user: %s' % str(req))

    # get user from MongoDB
    query = {'username':req['username']}
    result = mongo.db.users.find_one(query)

    if result is None:
        return jsonify({'msg':'user not found'}), 400
    return jsonify(result), 201


def generate_accountid():
    """Generates a globally unique alphanumerical accountid."""
    accountid = str(uuid.uuid4())
    while mongo.db.users.find_one({'accountid':accountid}) is not None:
        accountid = str(uuid.uuid4())
    return accountid


if __name__ == '__main__':
    for v in ['PORT', 'USER_DB_ADDR']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)

    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
