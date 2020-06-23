'''
Copyright 2018 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import datetime
import json
import logging
import os

from flask import Flask, abort, jsonify, make_response, redirect, \
    render_template, request, url_for
import requests
from requests.exceptions import HTTPError, RequestException
import jwt

APP = Flask(__name__)

@APP.route('/version', methods=['GET'])
def version():
    """
    Service version endpoint
    """
    return os.environ.get('VERSION'), 200

@APP.route('/ready', methods=['GET'])
def readiness():
    """
    Readiness probe
    """
    return 'ok', 200


@APP.route("/")
def root():
    """
    Renders home page or login page, depending on authentication status.
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if not verify_token(token):
        return login_page()
    return home()

@APP.route("/home")
def home():
    """
    Renders home page. Redirects to /login if token is not valid
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if not verify_token(token):
        # user isn't authenticated
        APP.logger.debug('User isn\'t authenticated. Redirecting to login page.')
        return redirect(url_for('login_page',
                                _external=True,
                                _scheme=APP.config['SCHEME']))
    token_data = jwt.decode(token, verify=False)
    display_name = token_data['name']
    username = token_data['user']
    account_id = token_data['acct']

    hed = {'Authorization': 'Bearer ' + token}
    # get balance
    balance = None
    try:
        url = '{}/{}'.format(APP.config["BALANCES_URI"], account_id)
        APP.logger.debug('Getting account balance.')
        response = requests.get(url=url, headers=hed, timeout=APP.config['BACKEND_TIMEOUT'])
        if response:
            balance = response.json()
    except (requests.exceptions.RequestException, ValueError) as err:
        APP.logger.error('Error getting account balance: %s', str(err))
    # get history
    transaction_list = None
    try:
        url = '{}/{}'.format(APP.config["HISTORY_URI"], account_id)
        APP.logger.debug('Getting transaction history.')
        response = requests.get(url=url, headers=hed, timeout=APP.config['BACKEND_TIMEOUT'])
        if response:
            transaction_list = response.json()
    except (requests.exceptions.RequestException, ValueError) as err:
        APP.logger.error('Error getting transaction history: %s', str(err))
    # get contacts
    contacts = []
    try:
        url = '{}/{}'.format(APP.config["CONTACTS_URI"], username)
        APP.logger.debug('Getting contacts.')
        response = requests.get(url=url, headers=hed, timeout=APP.config['BACKEND_TIMEOUT'])
        if response:
            contacts = response.json()
    except (requests.exceptions.RequestException, ValueError) as err:
        APP.logger.error('Error getting contacts: %s', str(err))

    _populate_contact_labels(account_id, transaction_list, contacts)

    return render_template('index.html',
                           history=transaction_list,
                           balance=balance,
                           name=display_name,
                           account_id=account_id,
                           contacts=contacts,
                           message=request.args.get('msg', None))


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
    APP.logger.debug('Populating contact labels.')
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


@APP.route('/payment', methods=['POST'])
def payment():
    """
    Submits payment request to ledgerwriter service

    Fails if:
    - token is not valid
    - basic validation checks fail
    - response code from ledgerwriter is not 201
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if not verify_token(token):
        # user isn't authenticated
        APP.logger.error('Error submitting payment: user is not authenticated.')
        return abort(401)
    try:
        account_id = jwt.decode(token, verify=False)['acct']
        recipient = request.form['account_num']
        if recipient == 'add':
            recipient = request.form['contact_account_num']
            label = request.form.get('contact_label', None)
            if label:
                # new contact. Add to contacts list
                _add_contact(label,
                             recipient,
                             APP.config['LOCAL_ROUTING'],
                             False)

        transaction_data = {"fromAccountNum": account_id,
                            "fromRoutingNum": APP.config['LOCAL_ROUTING'],
                            "toAccountNum": recipient,
                            "toRoutingNum": APP.config['LOCAL_ROUTING'],
                            "amount": int(float(request.form['amount']) * 100),
                            "uuid": request.form['uuid']}
        _submit_transaction(transaction_data)
        APP.logger.info('Payment initiated successfully.')
        return redirect(url_for('home',
                                msg='Payment initiated',
                                _external=True,
                                _scheme=APP.config['SCHEME']))

    except requests.exceptions.RequestException as err:
        APP.logger.error('Error submitting payment: %s', str(err))
    except UserWarning as warn:
        APP.logger.error('Error submitting payment: %s', str(warn))
        msg = 'Payment failed: {}'.format(str(warn))
        return redirect(url_for('home',
                                msg=msg,
                                _external=True,
                                _scheme=APP.config['SCHEME']))

    return redirect(url_for('home',
                            msg='Payment failed',
                            _external=True,
                            _scheme=APP.config['SCHEME']))

@APP.route('/deposit', methods=['POST'])
def deposit():
    """
    Submits deposit request to ledgerwriter service

    Fails if:
    - token is not valid
    - routing number == local routing number
    - response code from ledgerwriter is not 201
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if not verify_token(token):
        # user isn't authenticated
        APP.logger.error('Error submitting deposit: user is not authenticated.')
        return abort(401)
    try:
        # get account id from token
        account_id = jwt.decode(token, verify=False)['acct']
        if request.form['account'] == 'add':
            external_account_num = request.form['external_account_num']
            external_routing_num = request.form['external_routing_num']
            if external_routing_num == APP.config['LOCAL_ROUTING']:
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
                            "toRoutingNum": APP.config['LOCAL_ROUTING'],
                            "amount": int(float(request.form['amount']) * 100),
                            "uuid": request.form['uuid']}
        _submit_transaction(transaction_data)
        APP.logger.info('Deposit submitted successfully.')
        return redirect(url_for('home',
                                msg='Deposit accepted',
                                _external=True,
                                _scheme=APP.config['SCHEME']))

    except requests.exceptions.RequestException as err:
        APP.logger.error('Error submitting deposit: %s', str(err))
    except UserWarning as warn:
        APP.logger.error('Error submitting deposit: %s', str(warn))
        msg = 'Deposit failed: {}'.format(str(warn))
        return redirect(url_for('home',
                                msg=msg,
                                _external=True,
                                _scheme=APP.config['SCHEME']))

    return redirect(url_for('home',
                            msg='Deposit failed',
                            _external=True,
                            _scheme=APP.config['SCHEME']))

def _submit_transaction(transaction_data):
    APP.logger.debug('Submitting transaction.')
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    hed = {'Authorization': 'Bearer ' + token,
           'content-type': 'application/json'}
    resp = requests.post(url=APP.config["TRANSACTIONS_URI"],
                         data=jsonify(transaction_data).data,
                         headers=hed,
                         timeout=APP.config['BACKEND_TIMEOUT'])
    try:
        resp.raise_for_status() # Raise on HTTP Status code 4XX or 5XX
    except requests.exceptions.HTTPError as err:
        raise UserWarning(resp.text)


def _add_contact(label, acct_num, routing_num, is_external_acct=False):
    """
    Submits a new contact to the contact service.

    Raise: UserWarning  if the response status is 4xx or 5xx.
    """
    APP.logger.debug('Adding new contact.')
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    hed = {'Authorization': 'Bearer ' + token,
           'content-type': 'application/json'}
    contact_data = {
        'label': label,
        'account_num': acct_num,
        'routing_num': routing_num,
        'is_external': is_external_acct
    }
    token_data = jwt.decode(token, verify=False)
    url = '{}/{}'.format(APP.config["CONTACTS_URI"], token_data['user'])
    resp = requests.post(url=url,
                         data=jsonify(contact_data).data,
                         headers=hed,
                         timeout=APP.config['BACKEND_TIMEOUT'])
    try:
        resp.raise_for_status() # Raise on HTTP Status code 4XX or 5XX
    except requests.exceptions.HTTPError as err:
        raise UserWarning(resp.text)


@APP.route("/login", methods=['GET'])
def login_page():
    """
    Renders login page. Redirects to /home if user already has a valid token
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if verify_token(token):
        # already authenticated
        APP.logger.debug('User already authenticated. Redirecting to /home')
        return redirect(url_for('home',
                                _external=True,
                                _scheme=APP.config['SCHEME']))

    return render_template('login.html',
                           message=request.args.get('msg', None),
                           default_user=os.getenv('DEFAULT_USERNAME', ''),
                           default_password=os.getenv('DEFAULT_PASSWORD', ''))


@APP.route('/login', methods=['POST'])
def login():
    """
    Submits login request to userservice and saves resulting token

    Fails if userservice does not accept input username and password
    """
    return _login_helper(request.form['username'],
                         request.form['password'])


def _login_helper(username, password):
    try:
        APP.logger.debug('Logging in.')
        req = requests.get(url=APP.config["LOGIN_URI"],
                           params={'username': username, 'password': password})
        req.raise_for_status() # Raise on HTTP Status code 4XX or 5XX

        # login success
        token = req.json()['token'].encode('utf-8')
        claims = jwt.decode(token, verify=False)
        max_age = claims['exp'] - claims['iat']
        resp = make_response(redirect(url_for('home',
                                              _external=True,
                                              _scheme=APP.config['SCHEME'])))
        resp.set_cookie(APP.config['TOKEN_NAME'], token, max_age=max_age)
        APP.logger.info('Successfully logged in.')
        return resp
    except (RequestException, HTTPError) as err:
        APP.logger.error('Error logging in: %s', str(err))
    return redirect(url_for('login',
                            msg='Login Failed',
                            _external=True,
                            _scheme=APP.config['SCHEME']))


@APP.route("/signup", methods=['GET'])
def signup_page():
    """
    Renders signup page. Redirects to /login if token is not valid
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if verify_token(token):
        # already authenticated
        APP.logger.debug('User already authenticated. Redirecting to /home')
        return redirect(url_for('home',
                                _external=True,
                                _scheme=APP.config['SCHEME']))
    return render_template('signup.html')


@APP.route("/signup", methods=['POST'])
def signup():
    """
    Submits signup request to userservice

    Fails if userservice does not accept input form data
    """
    try:
        # create user
        APP.logger.debug('Creating new user.')
        resp = requests.post(url=APP.config["USERSERVICE_URI"],
                             data=request.form,
                             timeout=APP.config['BACKEND_TIMEOUT'])
        if resp.status_code == 201:
            # user created. Attempt login
            APP.logger.info('New user created.')
            return _login_helper(request.form['username'],
                                 request.form['password'])
    except requests.exceptions.RequestException as err:
        APP.logger.error('Error creating new user: %s', str(err))
    return redirect(url_for('login',
                            msg='Error: Account creation failed',
                            _external=True,
                            _scheme=APP.config['SCHEME']))

@APP.route('/logout', methods=['POST'])
def logout():
    """
    Logs out user by deleting token cookie and redirecting to login page
    """
    APP.logger.info('Logging out.')
    resp = make_response(redirect(url_for('login_page',
                                          _external=True,
                                          _scheme=APP.config['SCHEME'])))
    resp.delete_cookie(APP.config['TOKEN_NAME'])
    return resp


def verify_token(token):
    """
    Validates token using userservice public key
    """
    APP.logger.debug('Verifying token.')
    if token is None:
        return False
    try:
        jwt.decode(token, key=APP.config['PUBLIC_KEY'], algorithms='RS256', verify=True)
        APP.logger.debug('Token verified.')
        return True
    except jwt.exceptions.InvalidTokenError as err:
        APP.logger.error('Error validating token: %s', str(err))
        return False

# register html template formatters
def format_timestamp_day(timestamp):
    """ Format the input timestamp day in a human readable way """
    # TODO: time zones?
    date = datetime.datetime.strptime(timestamp, APP.config['TIMESTAMP_FORMAT'])
    return date.strftime('%d')

def format_timestamp_month(timestamp):
    """ Format the input timestamp month in a human readable way """
    # TODO: time zones?
    date = datetime.datetime.strptime(timestamp, APP.config['TIMESTAMP_FORMAT'])
    return date.strftime('%b')

def format_currency(int_amount):
    """ Format the input currency in a human readable way """
    if int_amount is None:
        return '$---'
    amount_str = '${:0,.2f}'.format(abs(float(int_amount)/100))
    if int_amount < 0:
        amount_str = '-' + amount_str
    return amount_str

# set up logger
APP.logger.handlers = logging.getLogger('gunicorn.error').handlers
APP.logger.setLevel(logging.getLogger('gunicorn.error').level)
APP.logger.info('Starting frontend service.')

# setup global variables
APP.config["TRANSACTIONS_URI"] = 'http://{}/transactions'.format(
    os.environ.get('TRANSACTIONS_API_ADDR'))
APP.config["USERSERVICE_URI"] = 'http://{}/users'.format(
    os.environ.get('USERSERVICE_API_ADDR'))
APP.config["BALANCES_URI"] = 'http://{}/balances'.format(
    os.environ.get('BALANCES_API_ADDR'))
APP.config["HISTORY_URI"] = 'http://{}/transactions'.format(
    os.environ.get('HISTORY_API_ADDR'))
APP.config["LOGIN_URI"] = 'http://{}/login'.format(
    os.environ.get('USERSERVICE_API_ADDR'))
APP.config["CONTACTS_URI"] = 'http://{}/contacts'.format(
    os.environ.get('CONTACTS_API_ADDR'))
APP.config['PUBLIC_KEY'] = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
APP.config['LOCAL_ROUTING'] = os.getenv('LOCAL_ROUTING_NUM')
APP.config['BACKEND_TIMEOUT'] = 3  # timeout in seconds for calls to the backend
APP.config['TOKEN_NAME'] = 'token'
APP.config['TIMESTAMP_FORMAT'] = '%Y-%m-%dT%H:%M:%S.%f%z'
APP.config['SCHEME'] = os.environ.get('SCHEME', 'http')

# register formater functions
APP.jinja_env.globals.update(format_currency=format_currency)
APP.jinja_env.globals.update(format_timestamp_month=format_timestamp_month)
APP.jinja_env.globals.update(format_timestamp_day=format_timestamp_day)
