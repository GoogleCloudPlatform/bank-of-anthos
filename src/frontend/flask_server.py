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
import sys

from flask import Flask, abort, jsonify, make_response, redirect, \
    render_template, request, url_for
import requests
import jwt


APP = Flask(__name__)

APP.config["TRANSACTIONS_URI"] = 'http://{}/new_transaction'.format(
    os.environ.get('TRANSACTIONS_API_ADDR'))
APP.config["USERSERVICE_URI"] = 'http://{}/create_user'.format(
    os.environ.get('USERSERVICE_API_ADDR'))
APP.config["BALANCES_URI"] = 'http://{}/get_balance'.format(
    os.environ.get('BALANCES_API_ADDR'))
APP.config["HISTORY_URI"] = 'http://{}/get_history'.format(
    os.environ.get('HISTORY_API_ADDR'))
APP.config["LOGIN_URI"] = 'http://{}/login'.format(
    os.environ.get('USERSERVICE_API_ADDR'))
APP.config["INTERNAL_CONTACTS_URI"] = 'http://{}/contacts'.format(
    os.environ.get('CONTACTS_API_ADDR'))
APP.config["EXTERNAL_ACCOUNTS_URI"] = 'http://{}/external'.format(
    os.environ.get('CONTACTS_API_ADDR'))


TOKEN_NAME = 'token'


@APP.route("/home")
@APP.route("/")
def home():
    """
    Renders homapage. Redirects to /login if token is not valid
    """
    token = request.cookies.get(TOKEN_NAME)
    if not verify_token(token):
        # user isn't authenticated
        return redirect(url_for('login_page'))

    token_data = jwt.decode(token, verify=False)
    display_name = token_data['name']
    account_id = token_data['acct']

    hed = {'Authorization': 'Bearer ' + token}
    # get balance
    balance = None
    try:
        req = requests.get(url=APP.config["BALANCES_URI"], headers=hed)
        balance = req.json()['balance']
    except requests.exceptions.RequestException as err:
        logging.error(str(err))
    # get history
    transaction_list = []
    try:
        req = requests.get(url=APP.config["HISTORY_URI"], headers=hed)
        transaction_list = req.json()['history']
    except requests.exceptions.RequestException as err:
        logging.error(str(err))
    # get contacts
    internal_list = []
    try:
        req = requests.get(url=APP.config["INTERNAL_CONTACTS_URI"],
                           headers=hed)
        internal_list = req.json()['account_list']
    except requests.exceptions.RequestException as err:
        logging.error(str(err))
    # get external accounts
    external_list = []
    try:
        req = requests.get(url=APP.config["EXTERNAL_ACCOUNTS_URI"],
                           headers=hed)
        external_list = req.json()['account_list']
    except requests.exceptions.RequestException as err:
        logging.error(str(err))

    return render_template('index.html',
                           history=transaction_list,
                           balance=balance,
                           name=display_name,
                           account_id=account_id,
                           external_accounts=external_list,
                           favorite_accounts=internal_list,
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
    token = request.cookies.get(TOKEN_NAME)
    if not verify_token(token):
        # user isn't authenticated
        return abort(401)
    try:
        account_id = jwt.decode(token, verify=False)['acct']
        recipient = request.form['account_num']
        if recipient == 'other':
            recipient = request.form['other_account_num']
        # convert amount to integer
        amount = int(float(request.form['amount']) * 100)
        # verify balance is sufficient
        hed = {'Authorization': 'Bearer ' + token}
        req = requests.get(url=APP.config["BALANCES_URI"], headers=hed)
        balance = req.json()['balance']
        if balance > amount:
            transaction_obj = {'fromRoutingNum':  LOCAL_ROUTING,
                               'fromAccountNum': account_id,
                               'toRoutingNum': LOCAL_ROUTING,
                               'toAccountNum': recipient,
                               'amount': amount}
            hed = {'Authorization': 'Bearer ' + token,
                   'content-type': 'application/json'}
            req = requests.post(url=APP.config["TRANSACTIONS_URI"],
                                data=jsonify(transaction_obj).data,
                                headers=hed,
                                timeout=3)
            if req.status_code == 201:
                return redirect(url_for('home', msg='Transaction initiated'))
    except requests.exceptions.RequestException as err:
        logging.error(str(err))
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
    token = request.cookies.get(TOKEN_NAME)
    if not verify_token(token):
        # user isn't authenticated
        return abort(401)
    try:
        # get account id from token
        account_id = jwt.decode(token, verify=False)['acct']

        # get data from form
        account_details = json.loads(request.form['account'])
        external_account_num = account_details['account_num']
        external_routing_num = account_details['routing_num']
        # convert amount to integer
        amount = int(float(request.form['amount']) * 100)

        # simulate transaction from external bank into user's account
        transaction_obj = {'fromRoutingNum':  external_routing_num,
                           'fromAccountNum': external_account_num,
                           'toRoutingNum': LOCAL_ROUTING,
                           'toAccountNum': account_id,
                           'amount': amount}
        hed = {'Authorization': 'Bearer ' + token,
               'content-type': 'application/json'}
        req = requests.post(url=APP.config["TRANSACTIONS_URI"],
                            data=jsonify(transaction_obj).data,
                            headers=hed,
                            timeout=3)
        if req.status_code == 201:
            return redirect(url_for('home', msg='Deposit accepted'))
    except requests.exceptions.RequestException as err:
        logging.error(str(err))
    return redirect(url_for('home', msg='Deposit failed'))


@APP.route("/login", methods=['GET'])
def login_page():
    """
    Renders login page. Redirects to /home if user already has a valid token
    """
    token = request.cookies.get(TOKEN_NAME)
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
    req = requests.get(url=APP.config["LOGIN_URI"],
                       params={'username': username, 'password': password})
    if req.status_code == 200:
        # login success
        token = req.json()['token'].encode('utf-8')
        claims = jwt.decode(token, verify=False)
        max_age = claims['exp'] - claims['iat']
        resp = make_response(redirect(url_for('home')))
        resp.set_cookie(TOKEN_NAME, token, max_age=max_age)
        return resp
    return redirect(url_for('login', msg='Login Failed'))


@APP.route("/signup", methods=['GET'])
def signup_page():
    """
    Renders signup page. Redirects to /login if token is not valid
    """
    token = request.cookies.get(TOKEN_NAME)
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

    # create user
    req = requests.post(url=APP.config["USERSERVICE_URI"],
                        data=request.form,
                        timeout=3)
    if req.status_code == 201:
        # user created. Attempt login
        return _login_helper(request.form['username'],
                             request.form['password'])
    logging.error(req.text)
    return redirect(url_for('login', msg='Error: Account creation failed'))


@APP.route('/logout', methods=['POST'])
def logout():
    """
    Logs out user by deleting token cookie and redirecting to login page
    """
    resp = make_response(redirect(url_for('login_page')))
    resp.delete_cookie(TOKEN_NAME)
    return resp


def verify_token(token):
    """
    Validates token using userservice public key
    """
    if token is None:
        return False
    try:
        jwt.decode(token, key=PUBLIC_KEY, algorithms='RS256', verify=True)
        return True
    except jwt.exceptions.InvalidTokenError as err:
        logging.error(err)
        return False


def format_timestamp(timestamp):
    """ Format the input timestamp in a human readable way """
    # TODO: time zones?
    date = datetime.datetime.fromtimestamp(float(timestamp))
    return date.strftime('%b %d, %Y')


def format_currency(int_amount):
    """ Format the input currency in a human readable way """
    if int_amount is None:
        return '$---'
    amount_str = '${:0,.2f}'.format(abs(float(int_amount)/100))
    if int_amount < 0:
        amount_str = '-' + amount_str
    return amount_str


if __name__ == '__main__':
    for v in ['PORT', 'TRANSACTIONS_API_ADDR', 'BALANCES_API_ADDR',
              'LOCAL_ROUTING_NUM', 'PUB_KEY_PATH', 'CONTACTS_API_ADDR',
              'USERSERVICE_API_ADDR']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            sys.exit(1)

    # setup global variables
    PUBLIC_KEY = open(os.environ.get('PUB_KEY_PATH'), 'r').read()
    LOCAL_ROUTING = os.getenv('LOCAL_ROUTING_NUM')

    # setup logger
    logging.basicConfig(level=logging.INFO,
                        format=('%(levelname)s|%(asctime)s'
                                '|%(pathname)s|%(lineno)d| %(message)s'),
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        )
    logging.getLogger().setLevel(logging.INFO)

    # register html template formatters
    APP.jinja_env.globals.update(format_timestamp=format_timestamp)
    APP.jinja_env.globals.update(format_currency=format_currency)

    # start serving requests
    logging.info("Starting flask.")
    APP.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
