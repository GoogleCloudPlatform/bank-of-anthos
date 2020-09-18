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
db manages interactions with the underlying database
"""

import logging
import random
import psycopg2
from psycopg2 import sql
from opentelemetry.ext.psycopg2 import Psycopg2Instrumentor


class UserDb:
    """
    UserDb provides a set of helper functions
    to handle db operations for the userservice
    """

    def __init__(self, uri, logger=logging):
        self.uri = uri
        self.logger = logger

        # Set up tracing autoinstrumentation with open telemetry
        Psycopg2Instrumentor().instrument()


    def add_user(self, user):
        """Add a user to the database.

        Params: user - a key/value dict of attributes describing a new user
                    {'username': username, 'password': password, ...}
        Raises: psycopg2.Error  if there was an issue with the database
        """
        with psycopg2.connect(self.uri) as conn:
            with conn.cursor() as curs:
                query = sql.SQL("INSERT INTO "
                                "users(accountid, username, passhash, "
                                "firstname, lastname, birthday, timezone, "
                                "address, state, zip, ssn) "
                                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                "%s, %s)")
                self.logger.debug("QUERY: %s", str(query))
                curs.execute(query, (
                    user.get('accountid'),
                    user.get('username'),
                    user.get('passhash'),
                    user.get('firstname'),
                    user.get('lastname'),
                    user.get('birthday'),
                    user.get('timezone'),
                    user.get('address'),
                    user.get('state'),
                    user.get('zip'),
                    user.get('ssn')))


    def generate_accountid(self):
        """Generates a globally unique alphanumerical accountid.

        Return: an alphanumerical accountid
        Raises: psycopg2.Error  if there was an issue with the database
        """
        self.logger.debug('Generating an account ID')
        accountid = None
        with psycopg2.connect(self.uri) as conn:
            with conn.cursor() as curs:
                query = sql.SQL("SELECT * FROM users "
                                "WHERE users.accountid = %s")
                self.logger.debug("QUERY: %s", str(query))
                while accountid is None:
                    accountid = str(random.randint(1e9, (1e10 - 1)))

                    curs.execute(query, (accountid,))
                    # If there already exists an account, try again.
                    if curs.fetchone() is not None:
                        accountid = None
                        self.logger.debug('RESULT: account ID already exists. Trying again')

        self.logger.debug('RESULT: account ID generated.')
        return accountid


    def get_user(self, username):
        """Get user data for the specified username.

        Params: username - the username of the user
        Return: a key/value dict of user attributes,
                {'username': username, 'accountid': accountid, ...}
                or None if that user does not exist
        Raises: psycopg2.Error  if there was an issue with the database
        """
        with psycopg2.connect(self.uri) as conn:
            with conn.cursor() as curs:
                query = sql.SQL("SELECT * FROM users "
                                "WHERE users.username = %s")
                self.logger.debug("QUERY: %s", str(query))
                curs.execute(query, (username,))

                result = curs.fetchone()

        self.logger.debug('RESULT: fetched user data for %s', username)
        return dict(result) if result is not None else None
