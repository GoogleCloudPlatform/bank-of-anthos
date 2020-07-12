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
from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, LargeBinary, Boolean


class AccountsDb:
    """
    AccountsDb provides a set of helper functions over SQLAlchemy
    to handle db operations for accountsservice.

    Defines 2 SQL Tables: users and contacts.
    """

    def __init__(self, uri, logger=logging):
        self.engine = create_engine(uri)
        self.logger = logger
        self.logger.debug('db.py initialize... ')
        self.users_table = Table(
            'users',
            MetaData(self.engine),
            Column('accountid', String, primary_key=True),
            Column('username', String, unique=True, nullable=False),
            Column('passhash', LargeBinary, nullable=False),
            Column('firstname', String, nullable=False),
            Column('lastname', String, nullable=False),
            Column('birthday', Date, nullable=False),
            Column('timezone', String, nullable=False),
            Column('address', String, nullable=False),
            Column('state', String, nullable=False),
            Column('zip', String, nullable=False),
            Column('ssn', String, nullable=False),
        )

        self.contacts_table = Table(
            "contacts",
            MetaData(self.engine),
            Column("username", String, nullable=False),
            Column("label", String, nullable=False),
            Column("account_num", String, nullable=False),
            Column("routing_num", String, nullable=False),
            Column("is_external", Boolean, nullable=False),
        )
        self.logger.debug('tables created. ready to add data.')


    def add_user(self, user):
        """Add a user to the database.

        Params: user - a key/value dict of attributes describing a new user
                    {'username': username, 'password': password, ...}
        Raises: SQLAlchemyError if there was an issue with the database
        """
        statement = self.users_table.insert().values(user)
        self.logger.debug('QUERY: %s', str(statement))
        with self.engine.connect() as conn:
            conn.execute(statement)

    def generate_accountid(self):
        """Generates a globally unique alphanumerical accountid."""
        self.logger.debug('Generating an account ID')
        accountid = None
        with self.engine.connect() as conn:
            while accountid is None:
                accountid = str(random.randint(1e9, (1e10 - 1)))

                statement = self.users_table.select().where(
                    self.users_table.c.accountid == accountid
                )
                self.logger.debug('QUERY: %s', str(statement))
                result = conn.execute(statement).first()
                # If there already exists an account, try again.
                if result is not None:
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
        Raises: SQLAlchemyError if there was an issue with the database
        """
        statement = self.users_table.select().where(self.users_table.c.username == username)
        self.logger.debug('QUERY: %s', str(statement))
        with self.engine.connect() as conn:
            result = conn.execute(statement).first()
        self.logger.debug('RESULT: fetched user data for %s', username)
        return dict(result) if result is not None else None


    def add_contact(self, contact):
        """Add a contact under the specified username.

        Params: user - a key/value dict of attributes describing a new contact
                    {'username': username, 'label': label, ...}
        Raises: SQLAlchemyError if there was an issue with the database
        """
        statement = self.contacts_table.insert().values(contact)
        self.logger.debug("QUERY: %s", str(statement))
        with self.engine.connect() as conn:
            conn.execute(statement)

    def get_contacts(self, username):
        """Get a list of contacts for the specified username.

        Params: username - the username of the user
        Return: a list of contacts in the form of key/value attribute dicts,
                [ {'label': contact1, ...}, {'label': contact2, ...}, ...]
        Raises: SQLAlchemyError if there was an issue with the database
        """
        contacts = list()
        statement = self.contacts_table.select().where(
            self.contacts_table.c.username == username
        )
        self.logger.debug("QUERY: %s", str(statement))
        with self.engine.connect() as conn:
            result = conn.execute(statement)
        for row in result:
            contact = {
                "label": row["label"],
                "account_num": row["account_num"],
                "routing_num": row["routing_num"],
                "is_external": row["is_external"],
            }
            contacts.append(contact)
        self.logger.debug("RESULT: Fetched %d contacts.", len(contacts))
        return contacts
