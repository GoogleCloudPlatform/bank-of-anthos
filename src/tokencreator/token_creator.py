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

import logging
import os

from datetime import datetime, timedelta

from flask import Flask, jsonify, request

import jwt

app = Flask(__name__)

@app.route('/get_token', methods=['GET'])
def get_token():
    username = request.args.get('username')
    password = request.args.get('password')
    # TODO: verify password hash against database
    payload = {'user':username,
               'acct':'1234',
               'iat': datetime.utcnow(),
               'exp': datetime.utcnow() + timedelta(seconds=_expiry_seconds)
               }
    encoded = jwt.encode(payload, _private_key, algorithm='RS256')

    return jsonify({'token':encoded}), 200


if __name__ == '__main__':
    for v in ['PORT', 'KEY_PATH', 'EXPIRY_SECONDS']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    _expiry_seconds = int(os.environ.get('EXPIRY_SECONDS'))
    _private_key = open(os.environ.get('KEY_PATH'), 'r').read()
    logging.info("Starting flask.")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
