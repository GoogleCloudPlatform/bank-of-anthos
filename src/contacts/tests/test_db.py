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
Tests for db module
"""
import random

import unittest

from contacts.db import ContactsDb
from contacts.tests.constants import EXAMPLE_CONTACT_DB_OBJ


class TestDb(unittest.TestCase):
    """
    Test cases for db module
    """

    def setUp(self):
        """Init db and create table before each test"""
        # init SQLAlchemy with sqllite in mem
        self.db = ContactsDb("sqlite:///:memory:")
        # create contacts table in mem
        self.db.contacts_table.create(self.db.engine)

    def test_add_contact_returns_none_no_exception(self):
        """test if a contact can be added"""
        contact = EXAMPLE_CONTACT_DB_OBJ.copy()
        # add contact to db
        self.db.add_contact(contact)

    def test_get_contact_returns_existing_contact(self):
        """test getting contacts for a user"""
        contact = EXAMPLE_CONTACT_DB_OBJ.copy()
        # create a contact with username bar
        contact["username"] = "bar"
        # add contact to db
        self.db.add_contact(contact)
        # get contact from db
        db_contact = self.db.get_contacts(contact["username"])
        # assert only one contact
        self.assertEqual(1, len(db_contact))
        # assert both contact objects are equal
        contact.pop("username")
        self.assertEqual(contact, db_contact[0])

    def test_get_contact_returns_multiple_existing_contacts(self):
        """test getting multiple contacts for a user"""
        contact = EXAMPLE_CONTACT_DB_OBJ.copy()
        # create a contact for username bar
        contact["username"] = "bar"
        # add n num_contacts contacts to db
        num_contacts = random.randrange(40)
        for i in range(num_contacts):
            contact["label"] = "label-{}".format(i)
            self.db.add_contact(contact)
        # get contact from db
        db_contact = self.db.get_contacts(contact["username"])
        # assert n contacts
        self.assertEqual(num_contacts, len(db_contact))

    def test_get_non_existent_contact_returns_empty(self):
        """test getting contacts for a non existent user"""
        # assert None when user does not exist
        self.assertEqual(0, len(self.db.get_contacts("baz")))
