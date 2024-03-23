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
from sqlalchemy import create_engine, MetaData, Table, Column, String, Boolean


class ContactsDb:
    """
    ContactsDb provides a set of helper functions over SQLAlchemy
    to handle db operations for contact service.
    """

    def __init__(self, uri, logger=logging):
        self.engine = create_engine(uri)
        self.logger = logger
        self.contacts_table = Table(
            "contacts",
            MetaData(self.engine),
            Column("username", String, nullable=False),
            Column("label", String, nullable=False),
            Column("account_num", String, nullable=False),
            Column("routing_num", String, nullable=False),
            Column("is_external", Boolean, nullable=False),
        )


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
