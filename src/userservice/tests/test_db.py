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
Tests for db module
"""

import unittest
from unittest.mock import patch

from sqlalchemy.exc import IntegrityError

from userservice.db import UserDb
from userservice.tests.constants import EXAMPLE_USER


class TestDb(unittest.TestCase):
    """
    Test cases for db module
    """

    def setUp(self):
        """Init db and create table before each test"""
        # init SQLAlchemy with sqllite in mem
        self.db = UserDb('sqlite:///:memory:')
        # create users table in mem
        self.db.users_table.create(self.db.engine)

    def test_add_user_returns_none_no_exception(self):
        """test if a user can be added"""
        user = EXAMPLE_USER.copy()
        # create a user with username foo
        user['username'] = 'foo'
        user['accountid'] = '1'
        # add user to db
        self.db.add_user(user)

    def test_add_same_user_raises_exception(self):
        """test if one user can be added twice"""
        user = EXAMPLE_USER.copy()
        # create a user with username bar
        user['username'] = 'bar'
        user['accountid'] = '2'
        # add bar_user to db
        self.db.add_user(user)
        # try to add same user again
        self.assertRaises(IntegrityError, self.db.add_user, user)

    def test_get_user_returns_existing_user(self):
        """test getting a user"""
        user = EXAMPLE_USER.copy()
        # create a user with username baz
        user['username'] = 'baz'
        user['accountid'] = '3'
        # add baz_user to db
        self.db.add_user(user)
        # get baz_user from db
        db_user = self.db.get_user(user['username'])
        # assert both user objects are equal
        self.assertEqual(user, db_user)

    def test_get_non_existent_user_returns_none(self):
        """test getting a user that does not exist"""
        # assert None when user does not exist
        self.assertIsNone(self.db.get_user('user1'))

    # mock random.randint to produce 4,5,6 on each invocation
    @patch('random.randint', side_effect=[4, 5, 6])
    def test_generate_account_id_ignores_existing_id_generates_new_id(self, mock_rand):
        """test generating account id"""
        user = EXAMPLE_USER.copy()
        # create a user with username qux
        user['username'] = 'qux'
        user['accountid'] = '4'
        # add qux_user to db
        # generate_account_id should return 5 now as 4 exists
        self.db.add_user(user)
        self.assertEqual('5', self.db.generate_accountid())
        # mock_rand was called twice, first generating 4, then 5
        self.assertEqual(2, mock_rand.call_count)
