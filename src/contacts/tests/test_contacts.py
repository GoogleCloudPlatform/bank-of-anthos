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
Tests for contacts
"""

import random
import unittest
import json
from unittest.mock import patch, mock_open

from sqlalchemy.exc import SQLAlchemyError

from contacts.contacts import create_app
from contacts.tests.constants import (
    EXAMPLE_CONTACT,
    EXAMPLE_USER,
    EXAMPLE_PUBLIC_KEY,
    EXAMPLE_HEADERS,
    EXAMPLE_USER_PAYLOAD,
    INVALID_ACCOUNT_NUMS,
    INVALID_LABELS,
    INVALID_ROUTING_NUMS,
)

def create_new_contact(**kwargs):
    """Helper method for creating new contacts from template"""
    example_contact = EXAMPLE_CONTACT.copy()
    example_contact.update(kwargs)
    return example_contact


class TestContacts(unittest.TestCase):
    """
    Tests cases for contacts
    """

    def setUp(self):
        """Setup Flask TestClient and mock contacts_db"""
        # mock opening files
        with patch("contacts.contacts.open", mock_open(read_data="foo")):
            # mock env vars
            with patch(
                "os.environ",
                {
                    "VERSION": "1",
                    "LOCAL_ROUTING": "123456789",
                    "PUBLIC_KEY": "1",
                    "ENABLE_TRACING": "false",
                },
            ):
                # mock db module as MagicMock, context manager handles cleanup
                with patch("contacts.contacts.ContactsDb") as mock_db:
                    self.mocked_db = mock_db
                    # get create flask app
                    self.flask_app = create_app()
                    # set testing config
                    self.flask_app.config["TESTING"] = True
                    # create test client
                    self.test_app = self.flask_app.test_client()
                    # set public key
                    self.flask_app.config["PUBLIC_KEY"] = EXAMPLE_PUBLIC_KEY
                    # mock return value of get_contacts to return empty
                    self.mocked_db.return_value.get_contacts.return_value = []

    def test_version_endpoint_returns_200_status_code_correct_version(self):
        """test if correct version is returned"""
        # generate a version
        version = str(random.randint(1, 9))
        # set version in Flask config
        self.flask_app.config["VERSION"] = version
        # send get request to test client
        response = self.test_app.get("/version")
        # assert 200 response code
        self.assertEqual(response.status_code, 200)
        # assert both versions are equal
        self.assertEqual(response.data, version.encode())

    def test_ready_endpoint_200_status_code_ok_string(self):
        """test if correct response is returned from readiness probe"""
        response = self.test_app.get("/ready")
        # assert 200 response code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"ok")

    def test_create_contact_201_status_code_correct_db_contact_object(self):
        """test adding a new contact to a users contact list"""
        # create example contact request
        example_contact = create_new_contact()
        # send request to test client
        response = self.test_app.post(
            "/contacts/{}".format(EXAMPLE_USER),
            headers=EXAMPLE_HEADERS,
            data=json.dumps(example_contact),
        )
        # assert 201 response code
        self.assertEqual(response.status_code, 201)
        # assert contact object added to database had the required fields
        # get the arg that contact_db.add_contact was called with
        contact_object = self.mocked_db.return_value.add_contact.call_args[0][0]
        # add username to example contact object
        example_contact["username"] = EXAMPLE_USER
        # assert all keys are equal
        self.assertEqual(contact_object, example_contact)

    def test_create_contact_409_status_code_add_same_user_to_contacts(self):
        """test adding a contact with same account_num and routing_num as the user"""
        # create example contact request and set account_num of contact equal to account_num of user
        invalid_contact = create_new_contact(account_num=EXAMPLE_USER_PAYLOAD["acct"])
        # set local routing number in service to match user routing number
        self.flask_app.config["LOCAL_ROUTING"] = invalid_contact["routing_num"]
        # send request to test client
        response = self.test_app.post(
            "/contacts/{}".format(EXAMPLE_USER),
            headers=EXAMPLE_HEADERS,
            data=json.dumps(invalid_contact),
        )
        # assert 409 response code
        self.assertEqual(response.status_code, 409)
        # assert we get correct error message
        self.assertEqual(
            response.data, b"may not add yourself to contacts"
        )

    def test_create_contact_409_status_code_duplicate_contact_with_diff_label(self,):
        """test adding a duplicate contact with same account_num
            and routing_num but different label"""
        # mock return value of get_contacts to return default EXAMPLE_CONTACT
        self.mocked_db.return_value.get_contacts.return_value = [
            create_new_contact()
        ]
        # create example contact request with new label
        duplicate_contact = create_new_contact(label="newlabel")
        # send request to test client
        response = self.test_app.post(
            "/contacts/{}".format(EXAMPLE_USER),
            headers=EXAMPLE_HEADERS,
            data=json.dumps(duplicate_contact),
        )
        # assert 409 response code
        self.assertEqual(response.status_code, 409)
        # assert we get correct error message
        self.assertEqual(
            response.data, b"account already exists as a contact"
        )

    def test_create_contact_409_status_code_duplicate_contact_with_same_label(self,):
        """test adding a duplicate contact with same label, different account/routing num"""
        # mock return value of get_contacts to return default EXAMPLE_CONTACT
        self.mocked_db.return_value.get_contacts.return_value = [
            create_new_contact()
        ]
        # create example contact request with new account_num and routing_num
        duplicate_contact = create_new_contact(account_num="1231231231", routing_num="123123123")
        # send request to test client
        response = self.test_app.post(
            "/contacts/{}".format(EXAMPLE_USER),
            headers=EXAMPLE_HEADERS,
            data=json.dumps(duplicate_contact),
        )
        # assert 409 response code
        self.assertEqual(response.status_code, 409)
        # assert we get correct error message
        self.assertEqual(
            response.data, b"contact already exists with that label"
        )

    def test_create_contact_400_status_code_invalid_account_number_less_than_ten_digits(self,):
        """test adding a contact with invalid account numbers"""
        # test for each invalid number in INVALID_ACCOUNT_NUMS
        for invalid_account_number in INVALID_ACCOUNT_NUMS:
            invalid_contact = create_new_contact(account_num=invalid_account_number)
            # send request to test client
            response = self.test_app.post(
                "/contacts/{}".format(EXAMPLE_USER),
                headers=EXAMPLE_HEADERS,
                data=json.dumps(invalid_contact),
            )
            # assert 400 response code
            self.assertEqual(response.status_code, 400)
            # assert we get correct error message
            self.assertEqual(response.data, b"invalid account number")

    def test_create_contact_400_status_code_invalid_routing_number_more_than_nine_digits(self,):
        """test adding a contact with invalid routing number"""
        # test for each invalid number in INVALID_ROUTING_NUMS
        for invalid_routing_number in INVALID_ROUTING_NUMS:
            invalid_contact = create_new_contact(routing_num=invalid_routing_number)
            # send request to test client
            response = self.test_app.post(
                "/contacts/{}".format(EXAMPLE_USER),
                headers=EXAMPLE_HEADERS,
                data=json.dumps(invalid_contact),
            )
            # assert 400 response code
            self.assertEqual(response.status_code, 400)
            # assert we get correct error message
            self.assertEqual(response.data, b"invalid routing number")

    def test_create_contact_400_status_code_is_external_routing_num_equals_local_routing(self,):
        """test adding a contact with same routing number as contact service local routing number"""
        # create example contact request
        example_contact = create_new_contact()
        # set contact service LOCAL_ROUTING to EXAMPLE_CONTACT routing_num
        self.flask_app.config["LOCAL_ROUTING"] = example_contact["routing_num"]
        # change contact as external
        example_contact["is_external"] = True
        # send request to test client
        response = self.test_app.post(
            "/contacts/{}".format(EXAMPLE_USER),
            headers=EXAMPLE_HEADERS,
            data=json.dumps(example_contact),
        )
        # assert 400 response code
        self.assertEqual(response.status_code, 400)
        # assert we get correct error message
        self.assertEqual(response.data, b"invalid routing number")

    def test_create_contact_400_status_code_invalid_labels(self,):
        """test adding a contact with invalid labels """
        # test for each invalid label in INVALID_LABELS
        for invalid_label in INVALID_LABELS:
            invalid_contact = create_new_contact(label=invalid_label)
            # send request to test client
            response = self.test_app.post(
                "/contacts/{}".format(EXAMPLE_USER),
                headers=EXAMPLE_HEADERS,
                data=json.dumps(invalid_contact),
            )
            # assert 400 response code
            self.assertEqual(response.status_code, 400)
            # assert we get correct error message
            self.assertEqual(response.data, b"invalid account label")

    def test_create_contact_500_add_contact_failure(self):
        """test adding a contact but throws SQL error when trying to add"""
        # mock return value of add_contact to throw an error
        self.mocked_db.return_value.add_contact.side_effect = SQLAlchemyError()
        # create example contact request
        example_contact = create_new_contact()
        # send request to test client
        response = self.test_app.post(
            "/contacts/{}".format(EXAMPLE_USER),
            headers=EXAMPLE_HEADERS,
            data=json.dumps(example_contact),
        )
        # assert 500 response code
        self.assertEqual(response.status_code, 500)
        # assert we get correct error message
        self.assertEqual(response.data, b"failed to add contact")

    def test_create_contact_400_add_contact_invalid_auth(self):
        """test adding a contact with invalid auth"""
        # mock return value of get_contacts to return empty
        self.mocked_db.return_value.get_contacts.return_value = []
        # modify header token to be incorrect
        invalid_token_header = EXAMPLE_HEADERS.copy()
        invalid_token_header["Authorization"] = "foo"
        # send request to test client
        response = self.test_app.post(
            "/contacts/{}".format(EXAMPLE_USER),
            headers=invalid_token_header,
            data=json.dumps(EXAMPLE_CONTACT),
        )
        # assert 401 response code
        self.assertEqual(response.status_code, 401)
        # assert we get correct error message
        self.assertEqual(response.data, b"authentication denied")

    def test_get_contacts_200_list_of_contacts(self):
        """test getting a list of contacts for a user"""
        # mock return value of get_contacts to return two values
        self.mocked_db.return_value.get_contacts.return_value = ["foo", "bar"]
        # send request to test client
        response = self.test_app.get(
            "/contacts/{}".format(EXAMPLE_USER), headers=EXAMPLE_HEADERS
        )
        # assert 200 response code
        self.assertEqual(response.status_code, 200)
        # assert get_contacts was called with the right args
        self.assertEqual(
            self.mocked_db.return_value.get_contacts.call_args[0][0],
            EXAMPLE_USER,
        )
        # assert we get right number of contacts
        self.assertEqual(len(response.json), 2)
        # assert we get right contacts
        self.assertEqual(response.json, ["foo", "bar"])

    def test_get_contacts_401_get_contacts_invalid_auth(self):
        """test getting a list of contacts for a user with invalid auth"""
        # mock return value of get_contacts to return empty list
        self.mocked_db.return_value.get_contacts.return_value = []
        # modify header token to be incorrect
        invalid_token_header = EXAMPLE_HEADERS.copy()
        invalid_token_header["Authorization"] = "foo"
        # send request to test client
        response = self.test_app.get(
            "/contacts/{}".format(EXAMPLE_USER), headers=invalid_token_header
        )
        # assert 200 response code
        self.assertEqual(response.status_code, 401)
        # assert we get correct error message
        self.assertEqual(response.data, b"authentication denied")

    def test_get_contacts_500_get_contacts_failure(self):
        """test getting contacts but throws SQL error"""
        # mock return value of get_contacts to throw an error
        self.mocked_db.return_value.get_contacts.side_effect = SQLAlchemyError()
        # send request to test client
        response = self.test_app.get(
            "/contacts/{}".format(EXAMPLE_USER), headers=EXAMPLE_HEADERS
        )
        # assert 200 response code
        self.assertEqual(response.status_code, 500)
        # assert we get correct error message
        self.assertEqual(
            response.data, b"failed to retrieve contacts list"
        )
