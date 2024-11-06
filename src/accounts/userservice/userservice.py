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
Userservice manages user account creation, user login, and related tasks
"""

import atexit
from datetime import datetime, timedelta
import logging
import os
import sys
import re
import time

#import bcrypt
import jwt
from flask import Flask, jsonify, request
import bleach
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from datetime import datetime, timedelta, timezone
from db import UserDb

# Import OpenTelemetry components
from opentelemetry import trace
#from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.trace import SpanKind
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider


# Initialize tracer provider and exporter
provider = TracerProvider(resource=Resource.create({SERVICE_NAME: "userservice"}))
exporter = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
span_processor = BatchSpanProcessor(exporter)
provider.add_span_processor(span_processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

def create_app():
    """Flask application factory to create instances of the Userservice Flask App"""
    app = Flask(__name__)

    # Instrument Flask with OpenTelemetry
 #   FlaskInstrumentor().instrument_app(app)

    # Cache the private key and public key at startup
    try:
        with tracer.start_as_current_span("cache_keys") as span:
            # Load private key as a string
            app.config['PRIVATE_KEY'] = open(os.environ.get('PRIV_KEY_PATH'), 'r').read()
            
            # Load public key as a string
            public_key_pem = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
            app.config['PUBLIC_KEY'] = public_key_pem

            # Load the public key into a cryptography object and get the bit size
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # Store the bit size of the public key in app.config
            app.config['PUBLIC_KEY_BIT_SIZE'] = public_key.key_size
            app.logger.info(f"Public key bit size set to {public_key.key_size}")
            span.set_attribute("keys.cached", True)
            span.set_attribute("public_key_bit_size", public_key.key_size)
            
            app.logger.info(f"Private and public keys loaded successfully.")
            
    except Exception as e:
        app.logger.critical(f"Failed to load keys: {e}")
        sys.exit(1)

    @app.route('/version', methods=['GET'])
    def version():
        """Service version endpoint"""
        with tracer.start_as_current_span("version", kind=SpanKind.SERVER) as version_span:
            version_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
            return app.config['VERSION'], 200

    @app.route('/ready', methods=['GET'])
    def readiness():
        """Readiness probe"""
        with tracer.start_as_current_span("readiness", kind=SpanKind.SERVER) as ready_span: 
            ready_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
            return 'ok', 200

    @app.route('/users', methods=['POST'])
    def create_user():
        """Create a user record."""
        with tracer.start_as_current_span("create_user", kind=SpanKind.SERVER):
            try:
                # Step 1: Sanitize user input
                with tracer.start_as_current_span("sanitize_input") as sanitize_span:
                    app.logger.debug('Sanitizing input.')
                    req = {k: bleach.clean(v) for k, v in request.form.items()}
                    sanitize_span.set_attribute("user_input.sanitized", True)

                # Step 2: Validate new user input
                with tracer.start_as_current_span("validate_new_user") as validate_span:
                    __validate_new_user(req)
                    validate_span.set_attribute("validation.success", True)

                # Step 3: Check if user already exists
                with tracer.start_as_current_span("check_user_exists") as check_span:
                    if users_db.get_user(req['username']) is not None:
                        raise NameError(f'user {req["username"]} already exists')
                    check_span.set_attribute("user_exists", False)

                # Step 4: Create password hash with PBKDF2
                with tracer.start_as_current_span("hash_password") as hash_span:
                    app.logger.debug("Creating password hash.")
                    password = req['password']
                    
                    # We can generate a smaller salt (8 bytes vs 16 that is the default)
                    salt = os.urandom(16)
                    
                    # Hash the password using PBKDF2 with SHA-256
                    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
                                                            
                    # Mark password hashing as completed
                    hash_span.set_attribute("password_hashed", True)
                    hash_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )

                # Step 5: Generate unique account ID
                with tracer.start_as_current_span("generate_accountid") as account_span:
                    accountid = users_db.generate_accountid()
                    account_span.set_attribute("accountid.generated", accountid)

                # Step 6: Create user data to add to the database
                user_data = {
                    'accountid': accountid,
                    'username': req['username'],
                    'passhash': hashed,  # The hashed password (binary)
                    'salt': salt,        # The salt (binary)
                    'firstname': req['firstname'],
                    'lastname': req['lastname'],
                    'birthday': req['birthday'],
                    'timezone': req['timezone'],
                    'address': req['address'],
                    'state': req['state'],
                    'zip': req['zip'],
                    'ssn': req['ssn'],
                }

                # Step 7: Add user to the database
                with tracer.start_as_current_span("db_add_user") as db_add_span:
                    app.logger.debug("Adding user to the database")
                    users_db.add_user(user_data)
                    db_add_span.set_attribute("user.added", True)
                app.logger.info("Successfully created user.")

            except UserWarning as warn:
                app.logger.error("Error creating new user: %s", str(warn))
                return str(warn), 400
            except NameError as err:
                app.logger.error("Error creating new user: %s", str(err))
                return str(err), 409
            except SQLAlchemyError as err:
                app.logger.error("Error creating new user: %s", str(err))
                return 'failed to create user', 500

            return jsonify({}), 201

    def __validate_new_user(req):
        with tracer.start_as_current_span("__validate_new_user"):
            app.logger.debug('validating create user request: %s', str(req))
            fields = (
                'username',
                'password',
                'password-repeat',
                'firstname',
                'lastname',
                'birthday',
                'timezone',
                'address',
                'state',
                'zip',
                'ssn',
            )
            if any(f not in req for f in fields):
                raise UserWarning('missing required field(s)')
            if any(not bool(req[f] or req[f].strip()) for f in fields):
                raise UserWarning('missing value for input field(s)')

            # Verify username contains only 2-15 alphanumeric or underscore characters
            if not re.match(r"\A[a-zA-Z0-9_]{2,15}\Z", req['username']):
                raise UserWarning('username must contain 2-15 alphanumeric characters or underscores')
            if not req['password'] == req['password-repeat']:
                raise UserWarning('passwords do not match')

    @app.route('/login', methods=['GET'])
    def login():
        """Login a user and return a JWT token"""
        current_span = trace.get_current_span()
        if current_span is not None:
           current_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
        with tracer.start_as_current_span("login", kind=SpanKind.SERVER) as span:
            span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
            try:

                # Step 1: Sanitize login input
                with tracer.start_as_current_span("sanitize_input") as sanitize_span:
                    app.logger.debug('Sanitizing login input.')
                    username = bleach.clean(request.args.get('username'))
                    password = bleach.clean(request.args.get('password'))
                    splunk_version = bleach.clean(str(request.args.get('splunk_version', '-'))).strip()
                    log_keys = True if splunk_version and splunk_version != '-' else False
                    #sanitize_span.set_attribute("version", splunk_version)
                    sanitize_span.set_attribute("username", username)
                    #sanitize_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )

                # Step 2: Get user data from the database
                with tracer.start_as_current_span("lookup_user_data") as get_user_span:
                    app.logger.debug('Getting the user data.')
                    #get_user_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
                    user = users_db.get_user(username)
                    if user is None:
                        raise LookupError('user {} does not exist'.format(username))
                    get_user_span.set_attribute("user_found", user is not None)

                # Step 3: Validate the password
                with tracer.start_as_current_span("validate_password") as password_span:
                    app.logger.debug('Validating the password.')
                    password_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
                    if not hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), user['salt'], 10000) == user['passhash']:   
                        password_span.set_attribute("password_valid", False)
                        raise PermissionError('invalid login')
                    password_span.set_attribute("password_valid", True)

                # Step 4: Generate JWT token
                with tracer.start_as_current_span("generate_session_token") as jwt_span:
                    try:
                        app.logger.debug('Creating session token.')
                        jwt_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
                        full_name = '{} {}'.format(user['firstname'], user['lastname'])
                        exp_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=app.config['EXPIRY_SECONDS'])
                    
                        payload = {
                            'user': username,
                            'acct': user['accountid'],
                            'name': full_name,
                            'iat':datetime.now(timezone.utc).replace(tzinfo=None) ,
                            'exp': exp_time,
                        }
                        # Sub-step: Create JWT payload
                        # with tracer.start_as_current_span("create_session_token_payload") as payload_span:
                        #     full_name = '{} {}'.format(user['firstname'], user['lastname'])
                        #     exp_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=app.config['EXPIRY_SECONDS'])
                          
                        #     payload = {
                        #         'user': username,
                        #         'acct': user['accountid'],
                        #         'name': full_name,
                        #         'iat':datetime.now(timezone.utc).replace(tzinfo=None) ,
                        #         'exp': exp_time,
                        #     }
                        #     payload_span.set_attribute("payload.user", username)
                        #     payload_span.set_attribute("payload.exp_time", exp_time.isoformat())
                        #     #payload_span.set_attribute("public_key_bit_size",  app.config.get('PUBLIC_KEY_BIT_SIZE', "None") )
                  
                           
                        # Sub-step: Encode JWT token using the cached private key
                        with tracer.start_as_current_span("encode_session_token") as encode_span:
                            # Start timing before the jwt.encode call
                            start_time = time.monotonic()
                            
                            # Perform the encoding
                            token = jwt.encode(payload, app.config['PRIVATE_KEY'], algorithm='RS256')
                            
                            # Calculate the duration
                            duration = time.monotonic() - start_time

                            # Log the encoding duration
                            if duration > 1.5:
                                app.logger.warn(f"Session key encoding duration exceeded threshold: {duration:.6f} seconds")
                            else:
                                app.logger.info(f"Session key encoding duration within acceptable range: {duration:.6f} seconds")
                            app.logger.info(f"Session key bit size equal to {app.config.get('PUBLIC_KEY_BIT_SIZE', 'None')} bits.")


                            # Add attributes to the span
                            encode_span.set_attribute("token_generated", True)
                            encode_span.set_attribute("encoding_duration_seconds", duration)
                            encode_span.set_attribute("public_key_bit_size", app.config.get('PUBLIC_KEY_BIT_SIZE', "None"))

                        # Log the success of the JWT generation
                        jwt_span.set_attribute("Session_Token.success", True)
                        app.logger.info('Session token successfully created.')

                    except Exception as e:
                        jwt_span.record_exception(e)
                        jwt_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        app.logger.error("Failed to create Session token: %s", str(e))
                        raise e

                app.logger.info('Login Successful.')
                return jsonify({'token': token}), 200

            except LookupError as err:
                app.logger.error('Error logging in: %s', str(err))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(err)))
                return str(err), 404

            except PermissionError as err:
                app.logger.error('Error logging in: %s', str(err))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(err)))
                return str(err), 401

            except SQLAlchemyError as err:
                app.logger.error('Error logging in: %s', str(err))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(err)))
                return 'failed to retrieve user information', 500

    @atexit.register
    def _shutdown():
        """Executed when web app is terminated."""
        with tracer.start_as_current_span("_shutdown"):
            app.logger.info("Stopping userservice.")

    # Set up logger
    app.logger.handlers = logging.getLogger('gunicorn.error').handlers
    app.logger.setLevel(logging.getLogger('gunicorn.error').level)
    app.logger.info('Starting userservice. v2.5')

    # Set up tracing and export spans to Cloud Trace.
    if os.environ['ENABLE_TRACING'] == "true" or trace.get_tracer_provider() is not None:
        app.logger.info("✅ Tracing enabled.")
    else:
        app.logger.info("🚫 Tracing disabled.")

    # Cache the keys once at app initialization
    app.config['VERSION'] = os.environ.get('VERSION')
    app.config['EXPIRY_SECONDS'] = int(os.environ.get('TOKEN_EXPIRY_SECONDS'))

    # Configure database connection and instrument SQLAlchemy
    try:
        with tracer.start_as_current_span("db_connect"):
            users_db = UserDb(os.environ.get("ACCOUNTS_DB_URI"), app.logger)
            # SQLAlchemyInstrumentor().instrument(engine=users_db.engine)
    except OperationalError as err:
        with tracer.start_as_current_span("db_connection_error"):
            app.logger.critical("users_db database connection failed: %s", str(err))
        sys.exit(1)

    return app


if __name__ == "__main__":
    # Create an instance of flask server when called directly
    USERSERVICE = create_app()
    USERSERVICE.run()                                         