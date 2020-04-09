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
        return redirect(url_for('login_page'))

    token_data = jwt.decode(token, verify=False)
    display_name = token_data['name']
    username = token_data['user']
    account_id = token_data['acct']

    hed = {'Authorization': 'Bearer ' + token}
    # get balance
    balance = None
    try:
        url = '{}/{}'.format(APP.config["BALANCES_URI"], account_id)
        response = requests.get(url=url, headers=hed, timeout=APP.config['BACKEND_TIMEOUT'])
        if response:
            balance = response.json()
    except (requests.exceptions.RequestException, ValueError) as err:
        APP.logger.error(str(err))
    # get history
    transaction_list = None
    try:
        url = '{}/{}'.format(APP.config["HISTORY_URI"], account_id)
        response = requests.get(url=url, headers=hed, timeout=APP.config['BACKEND_TIMEOUT'])
        if response:
            transaction_list = response.json()
    except (requests.exceptions.RequestException, ValueError) as err:
        APP.logger.error(str(err))
    # get contacts
    contacts = []
    try:
        url = '{}/{}'.format(APP.config["CONTACTS_URI"], username)
        response = requests.get(url=url, headers=hed, timeout=APP.config['BACKEND_TIMEOUT'])
        if response:
            contacts = response.json()
    except (requests.exceptions.RequestException, ValueError) as err:
        APP.logger.error(str(err))

    return render_template('index.html',
                           history=transaction_list,
                           balance=balance,
                           name=display_name,
                           account_id=account_id,
                           contacts=contacts,
                           message=request.args.get('msg', None))


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
                            "amount": int(float(request.form['amount']) * 100)}
        status_code = _submit_transaction(transaction_data)
        if status_code == 201:
            return redirect(url_for('home', msg='Transaction initiated'))
    except requests.exceptions.RequestException as err:
        APP.logger.error(str(err))
    return redirect(url_for('home', msg='Transaction failed'))

@APP.route('/deposit', methods=['POST'])
def deposit():
    """
    Submits deposit request to ledgerwriter service

    Fails if:
    - token is not valid
    - basic validation checks fail
    - response code from ledgerwriter is not 201
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if not verify_token(token):
        # user isn't authenticated
        return abort(401)
    try:
        # get account id from token
        account_id = jwt.decode(token, verify=False)['acct']
        if request.form['account'] == 'add':
            external_account_num = request.form['external_account_num']
            external_routing_num = request.form['external_routing_num']
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
                            "amount": int(float(request.form['amount']) * 100)}
        status_code = _submit_transaction(transaction_data)
        if status_code == 201:
            return redirect(url_for('home', msg='Deposit accepted'))
    except requests.exceptions.RequestException as err:
        APP.logger.error(str(err))

    return redirect(url_for('home', msg='Deposit failed'))

def _submit_transaction(transaction_data):
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    hed = {'Authorization': 'Bearer ' + token,
           'content-type': 'application/json'}
    req = requests.post(url=APP.config["TRANSACTIONS_URI"],
                        data=jsonify(transaction_data).data,
                        headers=hed,
                        timeout=APP.config['BACKEND_TIMEOUT'])
    return req.status_code


def _add_contact(label, acct_num, routing_num, is_external_acct=False):
    """
    Submits a new contact to the contact service
    """
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
    requests.post(url=url,
                  data=jsonify(contact_data).data,
                  headers=hed,
                  timeout=APP.config['BACKEND_TIMEOUT'])

@APP.route("/login", methods=['GET'])
def login_page():
    """
    Renders login page. Redirects to /home if user already has a valid token
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if verify_token(token):
        # already authenticated
        return redirect(url_for('home'))

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
        req = requests.get(url=APP.config["LOGIN_URI"],
                           params={'username': username, 'password': password})
        if req.status_code == 200:
            # login success
            token = req.json()['token'].encode('utf-8')
            claims = jwt.decode(token, verify=False)
            max_age = claims['exp'] - claims['iat']
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie(APP.config['TOKEN_NAME'], token, max_age=max_age)
            return resp
    except requests.exceptions.RequestException as err:
        APP.logger.error(str(err))
    return redirect(url_for('login', msg='Login Failed'))


@APP.route("/signup", methods=['GET'])
def signup_page():
    """
    Renders signup page. Redirects to /login if token is not valid
    """
    token = request.cookies.get(APP.config['TOKEN_NAME'])
    if verify_token(token):
        # already authenticated
        return redirect(url_for('home'))
    return render_template('signup.html')


@APP.route("/signup", methods=['POST'])
def signup():
    """
    Submits signup request to userservice

    Fails if userservice does not accept input form data
    """
    try:
        # create user
        resp = requests.post(url=APP.config["USERSERVICE_URI"],
                             data=request.form,
                             timeout=APP.config['BACKEND_TIMEOUT'])
        if resp.status_code == 201:
            # user created. Attempt login
            return _login_helper(request.form['username'],
                                 request.form['password'])
    except requests.exceptions.RequestException as err:
        APP.logger.error(str(err))
    return redirect(url_for('login', msg='Error: Account creation failed'))


@APP.route('/logout', methods=['POST'])
def logout():
    """
    Logs out user by deleting token cookie and redirecting to login page
    """
    resp = make_response(redirect(url_for('login_page')))
    resp.delete_cookie(APP.config['TOKEN_NAME'])
    return resp


def verify_token(token):
    """
    Validates token using userservice public key
    """
    if token is None:
        return False
    try:
        jwt.decode(token, key=APP.config['PUBLIC_KEY'], algorithms='RS256', verify=True)
        return True
    except jwt.exceptions.InvalidTokenError as err:
        APP.logger.debug(err)
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

# register formater functions
APP.jinja_env.globals.update(format_currency=format_currency)
APP.jinja_env.globals.update(format_timestamp_month=format_timestamp_month)
APP.jinja_env.globals.update(format_timestamp_day=format_timestamp_day)
