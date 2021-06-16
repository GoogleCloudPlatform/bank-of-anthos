# Copyright 2021 Google LLC
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
Example constants used in tests
"""
import random
import string
from datetime import datetime
from Crypto.PublicKey import RSA


def generate_rsa_key():
    """Generate priv,pub key pair for test"""
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

def get_random_string(length):
    """Generate random string of given length"""
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

EXAMPLE_PRIVATE_KEY, EXAMPLE_PUBLIC_KEY = generate_rsa_key()

TIMESTAMP_FORMAT = '%Y-%m-%d'
EXAMPLE_USER_REQUEST = {
    'username': 'jdoe',
    'password': 'pwd',
    'password-repeat': 'pwd',
    'firstname': 'John',
    'lastname': 'Doe',
    'birthday': '2000-01-01',
    'timezone': 'GMT+1',
    'address': '1600 Amphitheatre Parkway',
    'state': 'CA',
    'zip': '94043',
    'ssn': '123',
}
EXAMPLE_USER = {
    'accountid': '123',
    'username': 'jdoe',
    'passhash': b'hjfsrf#jrsfj',
    'firstname': 'John',
    'lastname': 'Doe',
    'birthday': datetime.strptime('2000-01-01', TIMESTAMP_FORMAT).date(),
    'timezone': 'GMT+1',
    'address': '1600 Amphitheatre Parkway',
    'state': 'CA',
    'zip': '94043',
    'ssn': '123',
}
EXPECTED_FIELDS = [
    'username',
    'password',
    'password-repeat',
    'firstname',
    'lastname',
    'birthday',
    'timezone',
    'address',
    'state',
    'zip',
    'ssn',
]

# Usernames must be >1 and <=15 chars, alphanumeric and underscores
INVALID_USERNAMES = [
    None, # null
    "", # empty string
    " ", # only space
    "b", # single character
    " user", # starting with space
    "*$&%($", # non alphanumeric characters
    "user*new", # alphanumeric with non alphanumeric characters
    "🏦💸", # emojis
    "user1💸", # alphanumeric with emojis
    get_random_string(16), # 16 characters
    " {}".format(get_random_string(15)), # 15 characters + leading space
    "{} ".format(get_random_string(15)), # 15 characters + trailing space
    "{}".format(get_random_string(100)), # 100 characters
    ]
