# Copyright 2020 Google LLC
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
from Crypto.PublicKey import RSA
import jwt

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

EXAMPLE_USER = "foo"

EXAMPLE_USER_PAYLOAD = {"user": EXAMPLE_USER, "acct": "1234512345"}

EXAMPLE_TOKEN = jwt.encode(
    EXAMPLE_USER_PAYLOAD, EXAMPLE_PRIVATE_KEY, algorithm="RS256"
)

EXAMPLE_HEADERS = {
    "Authorization": EXAMPLE_TOKEN,
    "content-type": "application/json",
}

EXAMPLE_CONTACT_DB_OBJ = {
    "username": "jdoe",
    "label": "foo",
    "account_num": "1234567890",
    "routing_num": "123456789",
    "is_external": False,
}

EXAMPLE_CONTACT = {
    "label": "jdoe",
    "account_num": "1234567890",
    "routing_num": "123456789",
    "is_external": False,
}

# Account numbers must be 10 digit numbers
INVALID_ACCOUNT_NUMS = [
    None, # null
    "", # empty
    "123123123", # 9 digit number
    "12312312312", # 11 digit number
    "foobarbazq", # 10 char string
    "123123123💸", # 9 digits and 1 emoji
    ]

# Labels must be >0 and <=30 chars, alphanumeric and spaces, can't start with space
INVALID_LABELS = [
    None, # null
    "", # empty string
    " ", # only space
    " label", # starting with space
    "*$&%($", # non alphanumeric characters
    "label*new", # alphanumeric with non alphanumeric characters
    "🏦💸", # emojis
    "label1💸", # alphanumeric with emojis
    get_random_string(31), # 31 characters
    " {}".format(get_random_string(30)), # 30 characters + leading space
    "{} ".format(get_random_string(30)), # 30 characters + trailing space
    "{}".format(get_random_string(100)), # 100 characters
    ]

# Routing numbers must be 9 digit numbers
INVALID_ROUTING_NUMS = [
    None, # null
    "", # empty
    "12312312", # 8 digit number
    "1231231231", # 10 digit number
    "foobarbaz", # 9 char string
    "12312312💸", # 8 digits and 1 emoji
    ]
