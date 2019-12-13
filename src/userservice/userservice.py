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

import bleach
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import logging
import os
from pymongo import ObjectId

app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://{}/users'.format(os.environ.get('USER_DB_ADDR'))
mongo = PyMongo(app)

@app.route('/create_user', methods=['POST'])
def create_user():
    """Create a new user.
    
    Generates an accountid. Fails if that username already exists.
    
    request:
      - username
      - password
    """
    req = request.get_json()
    logging.info('creating user: %s' % str(req))

    # check if user exists
    query = {'username':bleach.clean(req['username']}
    if mongo.db.users.find_one(query) is not None:
        return jsonify({'msg':'user already exists'}), 400

    # insert user in MongoDB
    accountid = generate_accountid()
    data = {'username':bleach.clean(req['username']),
            'password':bleach.clean(req['password']),
            'accountid':accountid}
    result = mongo.db.users.insert_one(data)
    if 'writeConcernError' in result:
        return jsonify(result['writeConcernError']), 500
    return jsonify({}), 201


@app.route('/get_user', methods=['GET'])
def get_user():
    """Get a user.

    Fails if there is no such user.
    
    request:
      - username

    response:
      - accountid
      - username
    """
    req = request.get_json()
    logging.info('getting user: %s' % str(req))

    # get user from MongoDB
    query = {'username':bleach.clean(req['username'])}
    fields = {'password':False}  # Omit the user password.
    result = mongo.db.users.find_one(query, fields)
    if result is None:
        return jsonify({'msg':'user not found'}), 400
    return jsonify(result), 201


@app.route('/delete_user', methods=['POST'])
def delete_user():
    """Delete a user.

    Fails if there is no such user.
    
    request:
      - username
    """
    req = request.get_json()
    logging.info('deleting user: %s' % str(req))

    # check if user exists
    query = {'username':bleach.clean(req['username']}
    if mongo.db.users.find_one(query) is not None:
        return jsonify({'msg':'user not found'}), 400

    # delete user from MongoDB
    data = {'username':bleach.clean(req['username'])}
    result = mongo.db.users.delete_one(data)
    return jsonify({}), 201


def generate_accountid():
    """Generates a globally unique alphanumerical accountid."""
    uuid = ObjectId()
    while mongo.db.users.find_one({'accountid':uuid.str}) is not None:
        uuid = ObjectId()
    return uuid.str


if __name__ == '__main__':
    for v in ['PORT', 'USER_DB_ADDR']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)

    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
