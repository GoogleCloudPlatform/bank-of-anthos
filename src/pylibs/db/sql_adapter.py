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

from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, LargeBinary, Boolean
import bcrypt
import logging
import random
from datetime import datetime

# timestamp format for birthdays
TIMESTAMP_FORMAT = '%Y-%m-%d'


class SqlAdapter:
    def __init__(self, uri):
        # connect to db
        self.engine = create_engine(uri)
        self.users_table = Table(
            'users',
            MetaData(self.engine),
            Column('accountid', String),
            Column('username', String),
            Column('passhash', LargeBinary),
            Column('firstname', String),
            Column('lastname', String),
            Column('birthday', Date),
            Column('timezone', String),
            Column('address', String),
            Column('state', String),
            Column('zip', String),
            Column('ssn', String),
        )
        self.contacts_table = Table(
            'contacts',
            MetaData(self.engine),
            Column('username', String),
            Column('label', String),
            Column('account_num', String),
            Column('routing_num', String),
            Column('is_external', Boolean),
        )
        # open a connection
        self.conn = self.engine.connect()

    def add_user(self, user):
        """Add a user to the database.

        Params: user - a key/value dict of attributes describing a new user
                    {'username': username, 'password': password, ...}
        Raises: SQLAlchemyError if there was an issue with the database
        """
        # Create password hash with salt
        password = user['password']
        salt = bcrypt.gensalt()
        passhash = bcrypt.hashpw(password.encode('utf-8'), salt)
        accountid = self._generate_accountid()

        # Add user to database
        data = {
            "accountid": accountid,
            "username": user['username'],
            "passhash": passhash,
            "firstname": user['firstname'],
            "lastname": user['lastname'],
            "birthday": datetime.strptime(user['birthday'], TIMESTAMP_FORMAT).date(),
            "timezone": user['timezone'],
            "address": user['address'],
            "state": user['state'],
            "zip": user['zip'],
            "ssn": user['ssn'],
        }
        statement = self.users_table.insert().values(data)
        logging.debug('QUERY: %s', str(statement))
        self.conn.execute(statement)

    def _generate_accountid(self):
        """Generates a globally unique alphanumerical accountid."""
        accountid = None
        while accountid is None:
            accountid = str(random.randint(1e9, (1e10 - 1)))

            statement = self.users_table.select().where(self.users_table.c.accountid == accountid)
            logging.debug('QUERY: %s', str(statement))
            result = self.conn.execute(statement).first()
            logging.debug('RESULT: %s', str(result))
            # If there already exists an account, try again.
            if result is not None:
                accountid = None
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
        logging.debug('QUERY: %s', str(statement))
        result = self.conn.execute(statement).first()
        logging.debug('RESULT: %s', str(result))

        return dict(result) if result is not None else None

    def close(self):
        """Executed when web app is terminated."""
        self.conn.close()

    def add_contact(self, username, contact):
        """Add a contact under the specified username.

        Params: username - the username of the user
                contact - a key/value dict of attributes describing a new contact
                        {'label': label, 'account_num': account_num, ...}
        Raises: SQLAlchemyError if there was an issue with the database
        """
        data = {
            "username": username,
            "label": contact['label'],
            "account_num": contact['account_num'],
            "routing_num": contact['routing_num'],
            "is_external": contact['is_external'],
        }
        statement = self.contacts_table.insert().values(data)
        logging.debug('QUERY: %s', str(statement))
        self.conn.execute(statement)

    def get_contacts(self, username):
        """Get a list of contacts for the specified username.

        Params: username - the username of the user
        Return: a list of contacts in the form of key/value attribute dicts,
                [ {'label': contact1, ...}, {'label': contact2, ...}, ...]
        Raises: SQLAlchemyError if there was an issue with the database
        """
        contacts = list()
        statement = self.contacts_table.select().where(self.contacts_table.c.username == username)
        logging.debug('QUERY: %s', str(statement))
        result = self.conn.execute(statement)
        logging.debug('RESULT: %s', str(result))
        for row in result:
            contact = {"label": row['label'], "account_num": row['account_num'], "routing_num": row['routing_num'], "is_external": row['is_external']}
            contacts.append(contact)

        return contacts
