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
db manages interactions with the underlying database
"""

import logging
import time
import psycopg2
from psycopg2 import sql
from opentelemetry.ext.psycopg2 import Psycopg2Instrumentor


class ContactsDb:
    """
    ContactsDb provides a set of helper functions over SQLAlchemy
    to handle db operations for contact service.
    """

    def __init__(self, uri, logger=logging):
        self.uri = uri
        self.logger = logger

        # Set up tracing autoinstrumentation with open telemetry
        Psycopg2Instrumentor().instrument()

    def add_contact(self, contact):
        """Add a contact under the specified username.

        Params: user - a key/value dict of attributes describing a new contact
                    {'username': username, 'label': label, ...}
        Raises: SQLAlchemyError if there was an issue with the database
        """
        with psycopg2.connect(self.uri) as conn:
            with conn.cursor() as curs:
                query = sql.SQL("INSERT INTO "
                    "contacts(username, label, account_num, routing_num, is_external) "
                    "VALUES (%s, %s, %s, %s, %s)")
                self.logger.debug("QUERY: %s", str(query))
                curs.execute(query, (
                    contact.get('username'),
                    contact.get('label'),
                    contact.get('account_num'),
                    contact.get('routing_num'),
                    contact.get('is_external')))

    def get_contacts(self, username):
        """Get a list of contacts for the specified username.

        Params: username - the username of the user
        Return: a list of contacts in the form of key/value attribute dicts,
                [ {'label': contact1, ...}, {'label': contact2, ...}, ...]
        Raises: SQLAlchemyError if there was an issue with the database
        """
        t = time.time()
        self.logger.info("db get: {}".format(t))
        contacts = list()
        with psycopg2.connect(self.uri) as conn:
            self.logger.debug("db connect: {}".format(time.time() - t))
            with conn.cursor() as curs:
                query = sql.SQL("SELECT * FROM contacts WHERE contacts.username = %s")
                self.logger.debug("QUERY: %s", str(query))
                result = curs.execute(query, (username,))
                self.logger.debug("db execute: {}".format(time.time() - t))

        if result is not None:
            for row in result:
                contact = {
                    "label": row["label"],
                    "account_num": row["account_num"],
                    "routing_num": row["routing_num"],
                    "is_external": row["is_external"],
                }
                contacts.append(contact)

        self.logger.debug("RESULT: Fetched %d contacts.", len(contacts))
        self.logger.debug("db return: {}".format(time.time() - t))
        return contacts
