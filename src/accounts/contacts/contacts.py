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
import atexit
import logging
import os
import re
import sys
import jwt
from flask import Flask, jsonify, request
import bleach
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from db import ContactsDb

# Initialize tracer
tracer = trace.get_tracer(__name__)

def create_app():
    """Flask application factory to create instances of the Contact Service Flask App"""
    app = Flask(__name__)

    @app.route("/version", methods=["GET"])
    def version():
        """Service version endpoint"""
        with tracer.start_as_current_span("version_endpoint", kind=SpanKind.SERVER):
            return app.config["VERSION"], 200

    @app.route("/ready", methods=["GET"])
    def ready():
        """Readiness probe."""
        with tracer.start_as_current_span("readiness_probe", kind=SpanKind.SERVER):
            return "ok", 200

    @app.route("/contacts/<username>", methods=["GET"])
    def get_contacts(username):
        """Retrieve the contacts list for the authenticated user."""
        with tracer.start_as_current_span("get_contacts", kind=SpanKind.SERVER) as span:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                token = auth_header.split(" ")[-1]
            else:
                token = ""
                span.set_attribute("error", "No authorization token provided")

            try:
                with tracer.start_as_current_span("decode_jwt") as jwt_span:
                    auth_payload = jwt.decode(token, key=app.config["PUBLIC_KEY"], algorithms="RS256")
                    jwt_span.set_attribute("username", auth_payload["user"])

                if username != auth_payload["user"]:
                    with tracer.start_as_current_span("username_mismatch") as mismatch_span:
                        mismatch_span.set_attribute("provided_username", username)
                        mismatch_span.set_attribute("payload_username", auth_payload["user"])
                        raise PermissionError("Username mismatch")

                with tracer.start_as_current_span("fetch_contacts"):
                    contacts_list = contacts_db.get_contacts(username)
                    app.logger.debug("Successfully retrieved contacts.")
                    return jsonify(contacts_list), 200

            except (PermissionError, jwt.exceptions.InvalidTokenError) as err:
                span.record_exception(err)
                app.logger.error("Error retrieving contacts list: %s", str(err))
                return "authentication denied", 401

            except SQLAlchemyError as err:
                span.record_exception(err)
                app.logger.error("Error retrieving contacts list: %s", str(err))
                return "failed to retrieve contacts list", 500

    @app.route("/contacts/<username>", methods=["POST"])
    def add_contact(username):
        """Add a new favorite account to user's contacts list"""
        with tracer.start_as_current_span("add_contact", kind=SpanKind.SERVER) as span:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                token = auth_header.split(" ")[-1]
            else:
                token = ""
                span.set_attribute("error", "No authorization token provided")

            try:
                with tracer.start_as_current_span("decode_jwt") as jwt_span:
                    auth_payload = jwt.decode(token, key=app.config["PUBLIC_KEY"], algorithms="RS256")
                    jwt_span.set_attribute("username", auth_payload["user"])

                if username != auth_payload["user"]:
                    with tracer.start_as_current_span("username_mismatch") as mismatch_span:
                        mismatch_span.set_attribute("provided_username", username)
                        mismatch_span.set_attribute("payload_username", auth_payload["user"])
                        raise PermissionError("Username mismatch")

                with tracer.start_as_current_span("sanitize_input") as sanitize_span:
                    req = {k: (bleach.clean(v) if isinstance(v, str) else v) for k, v in request.get_json().items()}
                    sanitize_span.set_attribute("user_input.sanitized", True)

                _validate_new_contact(req)
                _check_contact_allowed(username, auth_payload["acct"], req)

                # Create contact data to be added to the database
                contact_data = {
                    "username": username,
                    "label": req["label"],
                    "account_num": req["account_num"],
                    "routing_num": req["routing_num"],
                    "is_external": req["is_external"],
                }

                with tracer.start_as_current_span("db_add_contact"):
                    app.logger.debug("Adding new contact to the database.")
                    contacts_db.add_contact(contact_data)
                    span.set_attribute("contact_added", True)
                app.logger.info("Successfully added new contact.")
                return jsonify({}), 201

            except (PermissionError, jwt.exceptions.InvalidTokenError) as err:
                span.record_exception(err)
                app.logger.error("Error adding contact: %s", str(err))
                return "authentication denied", 401

            except UserWarning as warn:
                span.record_exception(warn)
                app.logger.error("Error adding contact: %s", str(warn))
                return str(warn), 400

            except ValueError as err:
                span.record_exception(err)
                app.logger.error("Error adding contact: %s", str(err))
                return str(err), 409

            except SQLAlchemyError as err:
                span.record_exception(err)
                app.logger.error("Error adding contact: %s", str(err))
                return "failed to add contact", 500

    def _validate_new_contact(req):
        """Check that this new contact request has valid fields"""
        with tracer.start_as_current_span("validate_new_contact") as span:
            app.logger.debug("validating add contact request: %s", str(req))
            fields = ("label", "account_num", "routing_num", "is_external")

            # Check if required fields are filled
            if any(f not in req for f in fields):
                span.add_event("missing_required_fields", attributes={"missing_fields": fields})
                raise UserWarning("missing required field(s)")

            # Validate account number (must be 10 digits)
            if req["account_num"] is None or not re.match(r"\A[0-9]{10}\Z", req["account_num"]):
                span.add_event("invalid_account_number", attributes={"account_number": req["account_num"]})
                raise UserWarning("invalid account number")

            # Validate routing number (must be 9 digits)
            if req["routing_num"] is None or not re.match(r"\A[0-9]{9}\Z", req["routing_num"]):
                span.add_event("invalid_routing_number", attributes={"routing_number": req["routing_num"]})
                raise UserWarning("invalid routing number")

            # Only allow external accounts to deposit
            if req["is_external"] and req["routing_num"] == app.config["LOCAL_ROUTING"]:
                span.add_event("invalid_external_routing_number", attributes={"routing_number": req["routing_num"]})
                raise UserWarning("invalid routing number")

            # Validate label
            if req["label"] is None or not re.match(r"^[0-9a-zA-Z][0-9a-zA-Z ]{0,29}$", req["label"]):
                span.add_event("invalid_account_label", attributes={"label": req["label"]})
                raise UserWarning("invalid account label")

    def _check_contact_allowed(username, accountid, req):
        """Check that this contact is allowed to be created"""
        with tracer.start_as_current_span("check_contact_allowed") as span:
            app.logger.debug("checking that this contact is allowed to be created: %s", str(req))

            # Don't allow self reference
            if req["account_num"] == accountid and req["routing_num"] == app.config["LOCAL_ROUTING"]:
                span.add_event("self_reference_blocked", attributes={"account_num": req["account_num"]})
                raise ValueError("may not add yourself to contacts")

            # Don't allow identical contacts
            for contact in contacts_db.get_contacts(username):
                if contact["account_num"] == req["account_num"] and contact["routing_num"] == req["routing_num"]:
                    span.add_event("duplicate_account_blocked", attributes={"account_num": req["account_num"]})
                    raise ValueError("account already exists as a contact")

                if contact["label"] == req["label"]:
                    span.add_event("duplicate_label_blocked", attributes={"label": req["label"]})
                    raise ValueError("contact already exists with that label")

    @atexit.register
    def _shutdown():
        """Executed when web app is terminated."""
        with tracer.start_as_current_span("_shutdown"):
            app.logger.info("Stopping contacts service.")

    # Set up logger
    app.logger.handlers = logging.getLogger("gunicorn.error").handlers
    app.logger.setLevel(logging.getLogger("gunicorn.error").level)
    app.logger.info("Starting contacts service.")

    # Set up tracing and export spans to Cloud Trace.
    if os.environ['ENABLE_TRACING'] == "true" or trace.get_tracer_provider() is not None:
        app.logger.info("✅ Tracing enabled.")
    else:
        app.logger.info("🚫 Tracing disabled.")

    # Set up global variables
    app.config["VERSION"] = os.environ.get("VERSION")
    app.config["LOCAL_ROUTING"] = os.environ.get("LOCAL_ROUTING_NUM")
    app.config["PUBLIC_KEY"] = open(os.environ.get("PUB_KEY_PATH"), "r").read()

    # Configure database connection
    try:
        with tracer.start_as_current_span("db_connect"):
            contacts_db = ContactsDb(os.environ.get("ACCOUNTS_DB_URI"), app.logger)
    except OperationalError as err:
        with tracer.start_as_current_span("db_connection_failed") as error_span:
            error_span.record_exception(err)
            app.logger.critical("database connection failed: %s", str(err))
        sys.exit(1)
    return app


if __name__ == "__main__":
    # Create an instance of flask server when called directly
    with tracer.start_as_current_span("create_flask_instance"):
        CONTACTS = create_app()

    with tracer.start_as_current_span("run_flask_instance"):
        CONTACTS.run()