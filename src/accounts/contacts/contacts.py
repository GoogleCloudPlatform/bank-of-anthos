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

"""Web service for handling linked user contacts.

Manages internal user contacts and external accounts.
"""

import atexit
import logging
import os
import re
import sys

import jwt
from flask import Flask, jsonify, request
import bleach
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from db import ContactsDb


def create_app():
    """Flask application factory to create instances
    of the Contact Service Flask App
    """
    app = Flask(__name__)

    # Disabling unused-variable for lines with route decorated functions
    # as pylint thinks they are unused
    # pylint: disable=unused-variable

    @app.route("/version", methods=["GET"])
    def version():
        """
        Service version endpoint
        """
        return app.config["VERSION"], 200

    @app.route("/ready", methods=["GET"])
    def ready():
        """Readiness probe."""
        return "ok", 200

    @app.route("/contacts/<username>", methods=["GET"])
    def get_contacts(username):
        """Retrieve the contacts list for the authenticated user.
        This list is used for populating Payment and Deposit fields.

        Return: a list of contacts
        """
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[-1]
        else:
            token = ""
        try:
            auth_payload = jwt.decode(
                token, key=app.config["PUBLIC_KEY"], algorithms="RS256"
            )
            if username != auth_payload["user"]:
                raise PermissionError

            contacts_list = contacts_db.get_contacts(username)
            app.logger.debug("Successfully retrieved contacts.")
            return jsonify(contacts_list), 200
        except (PermissionError, jwt.exceptions.InvalidTokenError) as err:
            app.logger.error("Error retrieving contacts list: %s", str(err))
            return "authentication denied", 401
        except SQLAlchemyError as err:
            app.logger.error("Error retrieving contacts list: %s", str(err))
            return "failed to retrieve contacts list", 500

    @app.route("/contacts/<username>", methods=["POST"])
    def add_contact(username):
        """Add a new favorite account to user's contacts list

        Fails if account or routing number are invalid
        or if label is not alphanumeric

        request fields:
        - account_num
        - routing_num
        - label
        - is_external
        """
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[-1]
        else:
            token = ""
        try:
            auth_payload = jwt.decode(
                token, key=app.config["PUBLIC_KEY"], algorithms="RS256"
            )
            if username != auth_payload["user"]:
                raise PermissionError
            req = {
                k: (bleach.clean(v) if isinstance(v, str) else v)
                for k, v in request.get_json().items()
            }
            _validate_new_contact(req)

            _check_contact_allowed(username, auth_payload["acct"], req)
            # Create contact data to be added to the database.
            contact_data = {
                "username": username,
                "label": req["label"],
                "account_num": req["account_num"],
                "routing_num": req["routing_num"],
                "is_external": req["is_external"],
            }
            # Add contact_data to database
            app.logger.debug("Adding new contact to the database.")
            contacts_db.add_contact(contact_data)
            app.logger.info("Successfully added new contact.")
            return jsonify({}), 201

        except (PermissionError, jwt.exceptions.InvalidTokenError) as err:
            app.logger.error("Error adding contact: %s", str(err))
            return "authentication denied", 401
        except UserWarning as warn:
            app.logger.error("Error adding contact: %s", str(warn))
            return str(warn), 400
        except ValueError as err:
            app.logger.error("Error adding contact: %s", str(err))
            return str(err), 409
        except SQLAlchemyError as err:
            app.logger.error("Error adding contact: %s", str(err))
            return "failed to add contact", 500

    def _validate_new_contact(req):
        """Check that this new contact request has valid fields"""
        app.logger.debug("validating add contact request: %s", str(req))
        # Check if required fields are filled
        fields = ("label", "account_num", "routing_num", "is_external")
        if any(f not in req for f in fields):
            raise UserWarning("missing required field(s)")

        # Validate account number (must be 10 digits)
        if req["account_num"] is None or not re.match(r"\A[0-9]{10}\Z", req["account_num"]):
            raise UserWarning("invalid account number")
        # Validate routing number (must be 9 digits)
        if req["routing_num"] is None or not re.match(r"\A[0-9]{9}\Z", req["routing_num"]):
            raise UserWarning("invalid routing number")
        # Only allow external accounts to deposit
        if (req["is_external"] and req["routing_num"] == app.config["LOCAL_ROUTING"]):
            raise UserWarning("invalid routing number")
        # Validate label
        # Must be >0 and <=30 chars, alphanumeric and spaces, can't start with space
        if req["label"] is None or not re.match(r"^[0-9a-zA-Z][0-9a-zA-Z ]{0,29}$", req["label"]):
            raise UserWarning("invalid account label")

    def _check_contact_allowed(username, accountid, req):
        """Check that this contact is allowed to be created"""
        app.logger.debug("checking that this contact is allowed to be created: %s", str(req))
        # Don't allow self reference
        if (req["account_num"] == accountid and req["routing_num"] == app.config["LOCAL_ROUTING"]):
            raise ValueError("may not add yourself to contacts")

        # Don't allow identical contacts
        for contact in contacts_db.get_contacts(username):
            if (contact["account_num"] == req["account_num"]
                    and contact["routing_num"] == req["routing_num"]):
                raise ValueError("account already exists as a contact")

            if contact["label"] == req["label"]:
                raise ValueError("contact already exists with that label")

    @atexit.register
    def _shutdown():
        """Executed when web app is terminated."""
        app.logger.info("Stopping contacts service.")

    # set up logger
    app.logger.handlers = logging.getLogger("gunicorn.error").handlers
    app.logger.setLevel(logging.getLogger("gunicorn.error").level)
    app.logger.info("Starting contacts service.")

    # Set up tracing and export spans to Cloud Trace.
    if os.environ['ENABLE_TRACING'] == "true":
        app.logger.info("✅ Tracing enabled.")
    else:
        app.logger.info("🚫 Tracing disabled.")

    # setup global variables
    app.config["VERSION"] = os.environ.get("VERSION")
    app.config["LOCAL_ROUTING"] = os.environ.get("LOCAL_ROUTING_NUM")
    app.config["PUBLIC_KEY"] = open(os.environ.get("PUB_KEY_PATH"), "r").read()

    # Configure database connection
    try:
        contacts_db = ContactsDb(os.environ.get("ACCOUNTS_DB_URI"), app.logger)
    except OperationalError:
        app.logger.critical("database connection failed")
        sys.exit(1)
    return app


if __name__ == "__main__":
    # Create an instance of flask server when called directly
    CONTACTS = create_app()
    CONTACTS.run()
