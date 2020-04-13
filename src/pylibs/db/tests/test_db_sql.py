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

import unittest
from sqlalchemy import MetaData
from sqlalchemy.exc import IntegrityError
from ..database_helper import DatabaseHelper
from .constants import EXAMPLE_USER, EXAMPLE_CONTACT
class TestDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.DB = DatabaseHelper('SQL', 'sqlite:///:memory:').database
        cls.DB.users_table.create(cls.DB.engine)
        cls.DB.contacts_table.create(cls.DB.engine)

    def test_add_user_foo(self):
        user=EXAMPLE_USER.copy()
        #create a user with username foo
        user['username']='foo'
        user['accountid']=self.DB.generate_accountid()
        self.DB.add_user(user)

    def test_add_same_user(self):
        user=EXAMPLE_USER.copy()
        #create a user with username bar
        user['username']='bar'
        user['accountid']=self.DB.generate_accountid()
        #add bar_user to db
        self.DB.add_user(user)
        #try to add same user again
        self.assertRaises(IntegrityError,self.DB.add_user,user)

    def test_get_user(self):
        user=EXAMPLE_USER.copy()
        #create a user with username bar
        user['username']='baz'
        user['accountid']=self.DB.generate_accountid()
        #add baz_user to db
        self.DB.add_user(user)
        #get baz_user from db
        db_user=self.DB.get_user(user['username'])
        #assert both user objects are equal
        self.assertEqual(user,db_user)

    def test_get_non_existent_user(self):
        #assert None when user does not exist
        self.assertIsNone(self.DB.get_user('user1'))

    def test_add_contact(self):
        #create a contact
        contact=EXAMPLE_CONTACT.copy()
        contact['username']='foo'
        #add contact to db
        self.DB.add_contact(contact)

    def test_get_contacts(self):
        #create a contact
        contact=EXAMPLE_CONTACT.copy()
        contact['username']='bar'
        #add contact to db
        self.DB.add_contact(contact)
        #get contact from db
        data=self.DB.get_contacts(contact['username'])
        #assert only one contact is returned
        self.assertEqual(len(data),1)
        #returned data will not have username key
        contact.pop('username',None)
        #assert both contact objects are equal
        self.assertEqual(contact,data[0])

    def test_get_non_existent_user_contacts(self):
        #assert empty list when user does not exist
        self.assertEqual(len(self.DB.get_contacts('user1')),0)
