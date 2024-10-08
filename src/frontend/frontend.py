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

"""Web service for frontend
"""

# Module imports
import concurrent.futures
import datetime
import json
import logging
import os
import socket
from decimal import Decimal, DecimalException
from time import sleep

import requests
from requests.exceptions import HTTPError, RequestException
import jwt
from flask import Flask, abort, jsonify, make_response, redirect, \
    render_template, request, url_for

from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.propagate import set_global_textmap
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor

# Local imports
from api_call import ApiCall, ApiRequest
from traced_thread_pool_executor import TracedThreadPoolExecutor

# Local constants
BALANCE_NAME = "balance"
CONTACTS_NAME = "contacts"
TRANSACTION_LIST_NAME = "transaction_list"

# pylint: disable-msg=too-many-locals
# pylint: disable-msg=too-many-branches
def create_app():
    """Flask application factory to create instances
    of the Frontend Flask App
    """
    app = Flask(__name__)

    # Disabling unused-variable for lines with route decorated functions
    # as pylint thinks they are unused
    # pylint: disable=unused-variable
    @app.route('/version', methods=['GET'])
    def version():
        """
        Service version endpoint
        """
        return os.environ.get('VERSION'), 200

    @app.route('/ready', methods=['GET'])
    def readiness():
        """
        Readiness probe
        """
        return 'ok', 200

    @app.route('/whereami', methods=['GET'])
    def whereami():
        """
        Returns the cluster name + zone name where this Pod is running.

        """
        return "Cluster: " + cluster_name + ", Pod: " + pod_name + ", Zone: " + pod_zone, 200

    @app.route("/")
    def root():
        """
        Renders home page or login page, depending on authentication status.
        """
        token = request.cookies.get(app.config['TOKEN_NAME'])
        if not verify_token(token):
            return login_page()
        return home()

    @app.route("/home")
    def home():
        """
        Renders home page. Redirects to /login if token is not valid
        """
        token = request.cookies.get(app.config['TOKEN_NAME'])
        if not verify_token(token):
            # user isn't authenticated
            app.logger.debug('User isn\'t authenticated. Redirecting to login page.')
            return redirect(url_for('login_page',
                                    _external=True,
                                    _scheme=app.config['SCHEME']))
        token_data = decode_token(token)
        display_name = token_data['name']
        username = token_data['user']
        account_id = token_data['acct']

        hed = {'Authorization': 'Bearer ' + token}

        api_calls = [
            # get balance
            ApiCall(display_name=BALANCE_NAME,
                    api_request=ApiRequest(url=f'{app.config["BALANCES_URI"]}/{account_id}',
                                           headers=hed,
                                           timeout=app.config['BACKEND_TIMEOUT']),
                    logger=app.logger),
            # get history
            ApiCall(display_name=TRANSACTION_LIST_NAME,
                    api_request=ApiRequest(url=f'{app.config["HISTORY_URI"]}/{account_id}',
                                           headers=hed,
                                           timeout=app.config['BACKEND_TIMEOUT']),
                    logger=app.logger),
            # get contacts
            ApiCall(display_name=CONTACTS_NAME,
                    api_request=ApiRequest(url=f'{app.config["CONTACTS_URI"]}/{username}',
                                           headers=hed,
                                           timeout=app.config['BACKEND_TIMEOUT']),
                    logger=app.logger)
        ]

        api_response = {BALANCE_NAME: None,
                        TRANSACTION_LIST_NAME: None,
                        CONTACTS_NAME: []}

        tracer = trace.get_tracer(__name__)
        with TracedThreadPoolExecutor(tracer, max_workers=3) as executor:
            futures = []

            future_to_api_call = {
                executor.submit(api_call.make_call):
                    api_call for api_call in api_calls
            }

            for future in concurrent.futures.as_completed(future_to_api_call):
                if future.result():
                    api_call = future_to_api_call[future]
                    api_response[api_call.display_name] = future.result().json()

        _populate_contact_labels(account_id,
                                 api_response[TRANSACTION_LIST_NAME],
                                 api_response[CONTACTS_NAME])

        return render_template('index.html',
                               account_id=account_id,
                               balance=api_response[BALANCE_NAME],
                               bank_name=os.getenv('BANK_NAME', 'Bank of Splunk'),
                               rum_realm=os.getenv('RUM_REALM','XX'),
                               rum_auth=os.getenv('RUM_AUTH','not-found'),
                               rum_app_name=os.getenv('RUM_APP_NAME','not-found'),
                               rum_environment=os.getenv('RUM_ENVIRONMENT','not-found'),
                               splunk_test=os.getenv('SPLUNK_TEST','A'),
                               splunk_version=os.getenv('SPLUNK_VERSION',"0.0.1"),
                               cluster_name=cluster_name,
                               contacts=api_response[CONTACTS_NAME],
                               cymbal_logo=os.getenv('CYMBAL_LOGO', 'false'),
                               history=api_response[TRANSACTION_LIST_NAME],
                               message=request.args.get('msg', None),
                               name=display_name,
                               platform=platform,
                               platform_display_name=platform_display_name,
                               pod_name=pod_name,
                               pod_zone=pod_zone)

    def _populate_contact_labels(account_id, transactions, contacts):
        """
        Populate contact labels for the passed transactions.

        Side effect:
            Take each transaction and set the 'accountLabel' field with the label of
            the contact each transaction was associated with. If there was no
            associated contact, set 'accountLabel' to None.
            If any parameter is None, nothing happens.

        Params: account_id - the account id for the user owning the transaction list
                transactions - a list of transactions as key/value dicts
                            [{transaction1}, {transaction2}, ...]
                contacts - a list of contacts as key/value dicts
                        [{contact1}, {contact2}, ...]
        """
        app.logger.debug('Populating contact labels.')
        if account_id is None or transactions is None or contacts is None:
            return

        # Map contact accounts to their labels. If no label found, default to None.
        contact_map = {c['account_num']: c.get('label') for c in contacts}

        # Populate the 'accountLabel' field. If no match found, default to None.
        for trans in transactions:
            if trans['toAccountNum'] == account_id:
                trans['accountLabel'] = contact_map.get(trans['fromAccountNum'])
            elif trans['fromAccountNum'] == account_id:
                trans['accountLabel'] = contact_map.get(trans['toAccountNum'])

    @app.route('/payment', methods=['POST'])
    def payment():
        """
        Submits payment request to ledgerwriter service

        Fails if:
        - token is not valid
        - basic validation checks fail
        - response code from ledgerwriter is not 201
        """
        token = request.cookies.get(app.config['TOKEN_NAME'])
        if not verify_token(token):
            # user isn't authenticated
            app.logger.error('Error submitting payment: user is not authenticated.')
            return abort(401)
        try:
            account_id = decode_token(token)['acct']
            recipient = request.form['account_num']
            if recipient == 'add':
                recipient = request.form['contact_account_num']
                label = request.form.get('contact_label', None)
                if label:
                    # new contact. Add to contacts list
                    _add_contact(label,
                                 recipient,
                                 app.config['LOCAL_ROUTING'],
                                 False)

            user_input = request.form['amount']
            payment_amount = int(Decimal(user_input) * 100)
            transaction_data = {"fromAccountNum": account_id,
                                "fromRoutingNum": app.config['LOCAL_ROUTING'],
                                "toAccountNum": recipient,
                                "toRoutingNum": app.config['LOCAL_ROUTING'],
                                "amount": payment_amount,
                                "uuid": request.form['uuid']}
            _submit_transaction(transaction_data)
            app.logger.info('Payment initiated successfully.')
            return redirect(code=303,
                            location=url_for('home',
                                             msg='Payment successful',
                                             _external=True,
                                             _scheme=app.config['SCHEME']))

        except requests.exceptions.RequestException as err:
            app.logger.error('Error submitting payment: %s', str(err))
        except UserWarning as warn:
            app.logger.error('Error submitting payment: %s', str(warn))
            msg = 'Payment failed: {}'.format(str(warn))
            return redirect(url_for('home',
                                    msg=msg,
                                    _external=True,
                                    _scheme=app.config['SCHEME']))
        except (ValueError, DecimalException) as num_err:
            app.logger.error('Error submitting payment: %s', str(num_err))
            msg = 'Payment failed: {} is not a valid number'.format(user_input)

        return redirect(url_for('home',
                                msg='Payment failed',
                                _external=True,
                                _scheme=app.config['SCHEME']))

    @app.route('/deposit', methods=['POST'])
    def deposit():
        """
        Submits deposit request to ledgerwriter service

        Fails if:
        - token is not valid
        - routing number == local routing number
        - response code from ledgerwriter is not 201
        """
        token = request.cookies.get(app.config['TOKEN_NAME'])
        if not verify_token(token):
            # user isn't authenticated
            app.logger.error('Error submitting deposit: user is not authenticated.')
            return abort(401)
        try:
            # get account id from token
            account_id = decode_token(token)['acct']
            if request.form['account'] == 'add':
                external_account_num = request.form['external_account_num']
                external_routing_num = request.form['external_routing_num']
                if external_routing_num == app.config['LOCAL_ROUTING']:
                    raise UserWarning("invalid routing number")
                external_label = request.form.get('external_label', None)
                if external_label:
                    # new contact. Add to contacts list
                    _add_contact(external_label,
                                 external_account_num,
                                 external_routing_num,
                                 True)
            else:
                account_details = json.loads(request.form['account'])
                external_account_num = account_details['account_num']
                external_routing_num = account_details['routing_num']

            transaction_data = {"fromAccountNum": external_account_num,
                                "fromRoutingNum": external_routing_num,
                                "toAccountNum": account_id,
                                "toRoutingNum": app.config['LOCAL_ROUTING'],
                                "amount": int(Decimal(request.form['amount']) * 100),
                                "uuid": request.form['uuid']}
            _submit_transaction(transaction_data)
            app.logger.info('Deposit submitted successfully.')
            return redirect(code=303,
                            location=url_for('home',
                                             msg='Deposit successful',
                                             _external=True,
                                             _scheme=app.config['SCHEME']))

        except requests.exceptions.RequestException as err:
            app.logger.error('Error submitting deposit: %s', str(err))
        except UserWarning as warn:
            app.logger.error('Error submitting deposit: %s', str(warn))
            msg = 'Deposit failed: {}'.format(str(warn))
            return redirect(url_for('home',
                                    msg=msg,
                                    _external=True,
                                    _scheme=app.config['SCHEME']))

        return redirect(url_for('home',
                                msg='Deposit failed',
                                _external=True,
                                _scheme=app.config['SCHEME']))

    def _submit_transaction(transaction_data):
        app.logger.debug('Submitting transaction.')
        token = request.cookies.get(app.config['TOKEN_NAME'])
        hed = {'Authorization': 'Bearer ' + token,
               'content-type': 'application/json'}
        resp = requests.post(url=app.config["TRANSACTIONS_URI"],
                             data=jsonify(transaction_data).data,
                             headers=hed,
                             timeout=app.config['BACKEND_TIMEOUT'])
        try:
            resp.raise_for_status()  # Raise on HTTP Status code 4XX or 5XX
        except requests.exceptions.HTTPError as http_request_err:
            raise UserWarning(resp.text) from http_request_err
        # Short delay to allow the transaction to propagate to balancereader
        # and transaction-history
        sleep(0.25)

    def _add_contact(label, acct_num, routing_num, is_external_acct=False):
        """
        Submits a new contact to the contact service.

        Raise: UserWarning  if the response status is 4xx or 5xx.
        """
        app.logger.debug('Adding new contact.')
        token = request.cookies.get(app.config['TOKEN_NAME'])
        hed = {'Authorization': 'Bearer ' + token,
               'content-type': 'application/json'}
        contact_data = {
            'label': label,
            'account_num': acct_num,
            'routing_num': routing_num,
            'is_external': is_external_acct
        }
        token_data = decode_token(token)
        url = '{}/{}'.format(app.config["CONTACTS_URI"], token_data['user'])
        resp = requests.post(url=url,
                             data=jsonify(contact_data).data,
                             headers=hed,
                             timeout=app.config['BACKEND_TIMEOUT'])
        try:
            resp.raise_for_status()  # Raise on HTTP Status code 4XX or 5XX
        except requests.exceptions.HTTPError as http_request_err:
            raise UserWarning(resp.text) from http_request_err

    @app.route("/login", methods=['GET'])
    def login_page():
        """
        Renders login page. Redirects to /home if user already has a valid token.
        If this is an oauth flow, then redirect to a consent form.
        """
        token = request.cookies.get(app.config['TOKEN_NAME'])
        response_type = request.args.get('response_type')
        client_id = request.args.get('client_id')
        app_name = request.args.get('app_name')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
        if ('REGISTERED_OAUTH_CLIENT_ID' in os.environ and
            'ALLOWED_OAUTH_REDIRECT_URI' in os.environ and
                response_type == 'code'):
            app.logger.debug('Login with response_type=code')
            if client_id != os.environ['REGISTERED_OAUTH_CLIENT_ID']:
                return redirect(url_for('login',
                                        msg='Error: Invalid client_id',
                                        _external=True,
                                        _scheme=app.config['SCHEME']))
            if redirect_uri != os.environ['ALLOWED_OAUTH_REDIRECT_URI']:
                return redirect(url_for('login',
                                        msg='Error: Invalid redirect_uri',
                                        _external=True,
                                        _scheme=app.config['SCHEME']))
            if verify_token(token):
                app.logger.debug('User already authenticated. Redirecting to /consent')
                return make_response(redirect(url_for('consent',
                                                      state=state,
                                                      redirect_uri=redirect_uri,
                                                      app_name=app_name,
                                                      _external=True,
                                                      _scheme=app.config['SCHEME'])))
        else:
            if verify_token(token):
                # already authenticated
                app.logger.debug('User already authenticated. Redirecting to /home')
                return redirect(url_for('home',
                                        _external=True,
                                        _scheme=app.config['SCHEME']))

        return render_template('login.html',
                               app_name=app_name,
                               bank_name=os.getenv('BANK_NAME', 'Bank of Splunk'),
                               rum_realm=os.getenv('RUM_REALM','XX'),
                               rum_auth=os.getenv('RUM_AUTH','not-found'),
                               rum_app_name=os.getenv('RUM_APP_NAME','not-found'),
                               rum_environment=os.getenv('RUM_ENVIRONMENT','not-found'),
                               splunk_test=os.getenv('SPLUNK_TEST','A'),
                               splunk_version=os.getenv('SPLUNK_VERSION',"0.0.1"),
                               cluster_name=cluster_name,
                               cymbal_logo=os.getenv('CYMBAL_LOGO', 'false'),
                               default_password=os.getenv('DEFAULT_PASSWORD', ''),
                               default_user=os.getenv('DEFAULT_USERNAME', ''),
                               message=request.args.get('msg', None),
                               platform=platform,
                               platform_display_name=platform_display_name,
                               pod_name=pod_name,
                               pod_zone=pod_zone,
                               redirect_uri=redirect_uri,
                               response_type=response_type,
                               state=state)

    @app.route('/login', methods=['POST'])
    def login():
        """
        Submits login request to userservice and saves resulting token

        Fails if userservice does not accept input username and password
        """
        return _login_helper(request.form['username'],
                             request.form['password'],
                             request.args)

    def _login_helper(username, password, request_args):
        try:
            app.logger.debug('Logging in.')
            req = requests.get(url=app.config["LOGIN_URI"],
                               params={'username': username, 'password': password},
                               timeout=app.config['BACKEND_TIMEOUT']*2)
            req.raise_for_status()  # Raise on HTTP Status code 4XX or 5XX

            # login success
            token = req.json()['token']
            claims = decode_token(token)
            max_age = claims['exp'] - claims['iat']

            if ('response_type' in request_args and
                'state' in request_args and
                'redirect_uri' in request_args and
                    request_args['response_type'] == 'code'):
                resp = make_response(redirect(url_for('consent',
                                                      state=request_args['state'],
                                                      redirect_uri=request_args['redirect_uri'],
                                                      app_name=request_args['app_name'],
                                                      _external=True,
                                                      _scheme=app.config['SCHEME'])))
            else:
                resp = make_response(redirect(url_for('home',
                                                      _external=True,
                                                      _scheme=app.config['SCHEME'])))
            resp.set_cookie(app.config['TOKEN_NAME'], token, max_age=max_age)
            app.logger.info('Successfully logged in.')
            return resp
        except (RequestException, HTTPError) as err:
            app.logger.error('Error logging in: %s', str(err))
        return redirect(url_for('login',
                                msg='Login Failed',
                                _external=True,
                                _scheme=app.config['SCHEME']))

    @app.route("/consent", methods=['GET'])
    def consent_page():
        """Renders consent page.

        Retrieves auth code if the user has
        already logged in and consented.
        """
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
        app_name = request.args.get('app_name')
        token = request.cookies.get(app.config['TOKEN_NAME'])
        consented = request.cookies.get(app.config['CONSENT_COOKIE'])
        if verify_token(token):
            if consented == "true":
                app.logger.debug('User consent already granted.')
                resp = _auth_callback_helper(state, redirect_uri, token)
                return resp

            return render_template('consent.html',
                                    app_name=app_name,
                                    bank_name=os.getenv('BANK_NAME', 'Bank of Splunk'),
                                    rum_realm=os.getenv('RUM_REALM','XX'),
                                    rum_auth=os.getenv('RUM_AUTH','not-found'),
                                    rum_app_name=os.getenv('RUM_APP_NAME','not-found'),
                                    rum_environment=os.getenv('RUM_ENVIRONMENT','not-found'),
                                    splunk_test=os.getenv('SPLUNK_TEST','A'),
                                    splunk_version=os.getenv('SPLUNK_VERSION',"0.0.1"),
                                    cluster_name=cluster_name,
                                    cymbal_logo=os.getenv('CYMBAL_LOGO', 'false'),
                                    platform=platform,
                                    platform_display_name=platform_display_name,
                                    pod_name=pod_name,
                                    pod_zone=pod_zone,
                                    redirect_uri=redirect_uri,
                                    state=state)

        return make_response(redirect(url_for('login',
                                              response_type="code",
                                              state=state,
                                              redirect_uri=redirect_uri,
                                              app_name=app_name,
                                              _external=True,
                                              _scheme=app.config['SCHEME'])))

    @app.route('/consent', methods=['POST'])
    def consent():
        """
        Check consent, write cookie if yes, and redirect accordingly
        """
        consent = request.args['consent']
        state = request.args['state']
        redirect_uri = request.args['redirect_uri']
        token = request.cookies.get(app.config['TOKEN_NAME'])

        app.logger.debug('Checking consent. consent: %s', consent)

        if consent == "true":
            app.logger.info('User consent granted.')
            resp = _auth_callback_helper(state, redirect_uri, token)
            resp.set_cookie(app.config['CONSENT_COOKIE'], 'true')
        else:
            app.logger.info('User consent denied.')
            resp = make_response(redirect(redirect_uri + '#error=access_denied', 302))
        return resp

    def _auth_callback_helper(state, redirect_uri, token):
        try:
            app.logger.debug('Retrieving authorization code.')
            callback_response = requests.post(url=redirect_uri,
                                              data={'state': state, 'id_token': token},
                                              timeout=app.config['BACKEND_TIMEOUT'],
                                              allow_redirects=False)
            if callback_response.status_code == requests.codes.found:
                app.logger.info('Successfully retrieved auth code.')
                location = callback_response.headers['Location']
                return make_response(redirect(location, 302))

            app.logger.error('Unexpected response status: %s', callback_response.status_code)
            return make_response(redirect(redirect_uri + '#error=server_error', 302))
        except requests.exceptions.RequestException as err:
            app.logger.error('Error retrieving auth code: %s', str(err))
        return make_response(redirect(redirect_uri + '#error=server_error', 302))

    @app.route("/signup", methods=['GET'])
    def signup_page():
        """
        Renders signup page. Redirects to /login if token is not valid
        """
        token = request.cookies.get(app.config['TOKEN_NAME'])
        if verify_token(token):
            # already authenticated
            app.logger.debug('User already authenticated. Redirecting to /home')
            return redirect(url_for('home',
                                    _external=True,
                                    _scheme=app.config['SCHEME']))
        return render_template('signup.html',
                               bank_name=os.getenv('BANK_NAME', 'Bank of Splunk'),
                               rum_realm=os.getenv('RUM_REALM','XX'),
                               rum_auth=os.getenv('RUM_AUTH','not-found'),
                               rum_app_name=os.getenv('RUM_APP_NAME','not-found'),
                               rum_environment=os.getenv('RUM_ENVIRONMENT','not-found'),
                               splunk_test=os.getenv('SPLUNK_TEST','A'),
                               splunk_version=os.getenv('SPLUNK_VERSION',"0.0.1"),
                               cluster_name=cluster_name,
                               cymbal_logo=os.getenv('CYMBAL_LOGO', 'false'),
                               platform=platform,
                               platform_display_name=platform_display_name,
                               pod_name=pod_name,
                               pod_zone=pod_zone)

    @app.route("/signup", methods=['POST'])
    def signup():
        """
        Submits signup request to userservice

        Fails if userservice does not accept input form data
        """
        try:
            # create user
            app.logger.debug('Creating new user.')
            resp = requests.post(url=app.config["USERSERVICE_URI"],
                                 data=request.form,
                                 timeout=app.config['BACKEND_TIMEOUT'])
            if resp.status_code == 201:
                # user created. Attempt login
                app.logger.info('New user created.')
                return _login_helper(request.form['username'],
                                     request.form['password'],
                                     request.args)
        except requests.exceptions.RequestException as err:
            app.logger.error('Error creating new user: %s', str(err))
        return redirect(url_for('login',
                                msg='Error: Account creation failed',
                                _external=True,
                                _scheme=app.config['SCHEME']))

    @app.route('/logout', methods=['POST'])
    def logout():
        """
        Logs out user by deleting token cookie and redirecting to login page
        """
        app.logger.info('Logging out.')
        resp = make_response(redirect(url_for('login_page',
                                              _external=True,
                                              _scheme=app.config['SCHEME'])))
        resp.delete_cookie(app.config['TOKEN_NAME'])
        resp.delete_cookie(app.config['CONSENT_COOKIE'])
        return resp

    def decode_token(token):
        return jwt.decode(algorithms='RS256',
                          jwt=token,
                          options={"verify_signature": False})

    def verify_token(token):
        """
        Validates token using userservice public key
        """
        app.logger.debug('Verifying token.')
        if token is None:
            return False
        try:
            jwt.decode(algorithms='RS256',
                       jwt=token,
                       key=app.config['PUBLIC_KEY'],
                       options={"verify_signature": True})
            app.logger.debug('Token verified.')
            return True
        except jwt.exceptions.InvalidTokenError as err:
            app.logger.error('Error validating token: %s', str(err))
            return False

    # register html template formatters
    def format_timestamp_day(timestamp):
        """ Format the input timestamp day in a human readable way """
        # TODO: time zones?
        date = datetime.datetime.strptime(timestamp, app.config['TIMESTAMP_FORMAT'])
        return date.strftime('%d')

    def format_timestamp_month(timestamp):
        """ Format the input timestamp month in a human readable way """
        # TODO: time zones?
        date = datetime.datetime.strptime(timestamp, app.config['TIMESTAMP_FORMAT'])
        return date.strftime('%b')

    def format_currency(int_amount):
        """ Format the input currency in a human readable way """
        if int_amount is None:
            return '$---'
        amount_str = '${:0,.2f}'.format(abs(Decimal(int_amount)/100))
        if int_amount < 0:
            amount_str = '-' + amount_str
        return amount_str

    # set up global variables
    app.config["TRANSACTIONS_URI"] = 'http://{}/transactions'.format(
        os.environ.get('TRANSACTIONS_API_ADDR'))
    app.config["USERSERVICE_URI"] = 'http://{}/users'.format(
        os.environ.get('USERSERVICE_API_ADDR'))
    app.config["BALANCES_URI"] = 'http://{}/balances'.format(
        os.environ.get('BALANCES_API_ADDR'))
    app.config["HISTORY_URI"] = 'http://{}/transactions'.format(
        os.environ.get('HISTORY_API_ADDR'))
    app.config["LOGIN_URI"] = 'http://{}/login'.format(
        os.environ.get('USERSERVICE_API_ADDR'))
    app.config["CONTACTS_URI"] = 'http://{}/contacts'.format(
        os.environ.get('CONTACTS_API_ADDR'))
    app.config['PUBLIC_KEY'] = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    app.config['LOCAL_ROUTING'] = os.getenv('LOCAL_ROUTING_NUM')
    # timeout in seconds for calls to the backend
    app.config['BACKEND_TIMEOUT'] = int(os.getenv('BACKEND_TIMEOUT', '4'))
    app.config['TOKEN_NAME'] = 'token'
    app.config['CONSENT_COOKIE'] = 'consented'
    app.config['TIMESTAMP_FORMAT'] = '%Y-%m-%dT%H:%M:%S.%f%z'
    app.config['SCHEME'] = os.environ.get('SCHEME', 'http')

    # where am I?
    metadata_server = os.getenv('METADATA_SERVER', 'metadata.google.internal')
    metadata_url = f'http://{metadata_server}/computeMetadata/v1/'
    metadata_headers = {'Metadata-Flavor': 'Google'}

    # get GKE cluster name
    cluster_name = os.getenv('CLUSTER_NAME', 'unknown')
    try:
        req = requests.get(metadata_url + 'instance/attributes/cluster-name',
                           headers=metadata_headers,
                           timeout=app.config['BACKEND_TIMEOUT'])
        if req.ok:
            cluster_name = str(req.text)
    except (RequestException, HTTPError) as err:
        app.logger.warning(
            "Unable to retrieve cluster name from metadata server %s.", metadata_server)

    # get GKE pod name
    pod_name = "unknown"
    pod_name = socket.gethostname()

    # get GKE node zone
    pod_zone = os.getenv('POD_ZONE', 'unknown')
    try:
        req = requests.get(metadata_url + 'instance/zone',
                           headers=metadata_headers,
                           timeout=app.config['BACKEND_TIMEOUT'])
        if req.ok:
            pod_zone = str(req.text.split("/")[3])
    except (RequestException, HTTPError) as err:
        app.logger.warning("Unable to retrieve zone from metadata server %s.", metadata_server)

    # register formater functions
    app.jinja_env.globals.update(format_currency=format_currency)
    app.jinja_env.globals.update(format_timestamp_month=format_timestamp_month)
    app.jinja_env.globals.update(format_timestamp_day=format_timestamp_day)

    # Set up logging
    app.logger.handlers = logging.getLogger('gunicorn.error').handlers
    app.logger.setLevel(logging.getLogger('gunicorn.error').level)
    app.logger.info('Starting frontend service.')

    # Set up tracing and export spans to Cloud Trace.
    if os.environ['ENABLE_TRACING'] == "true":
        app.logger.info("✅ Tracing enabled.")
        trace.set_tracer_provider(TracerProvider())
        cloud_trace_exporter = CloudTraceSpanExporter()
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(cloud_trace_exporter)
        )
        set_global_textmap(CloudTraceFormatPropagator())
        # Add tracing auto-instrumentation for Flask, jinja and requests
        FlaskInstrumentor().instrument_app(app)
        RequestsInstrumentor().instrument()
        Jinja2Instrumentor().instrument()
    else:
        app.logger.info("🚫 Tracing disabled.")

    platform = os.getenv('ENV_PLATFORM', None)
    platform_display_name = None
    if platform is not None:
        platform = platform.lower()
        if platform not in ['alibaba', 'aws', 'azure', 'gcp', 'local', 'onprem']:
            app.logger.error("Platform '%s' not supported, defaulting to None", platform)
            platform = None
        else:
            app.logger.info("Platform is set to '%s'", platform)
            if platform == 'alibaba':
                platform_display_name = "Alibaba Cloud"
            elif platform == 'aws':
                platform_display_name = "AWS"
            elif platform == 'azure':
                platform_display_name = "Azure"
            elif platform == 'gcp':
                platform_display_name = "Google Cloud"
            elif platform == 'local':
                platform_display_name = "Local"
            elif platform == 'onprem':
                platform_display_name = "On-Premises"
    else:
        app.logger.info("ENV_PLATFORM environment variable is not set")

    return app


if __name__ == "__main__":
    # Create an instance of flask server when called directly
    FRONTEND = create_app()
    FRONTEND.run()
