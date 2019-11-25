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

import logging

from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)


# handle requests to the server
@app.route("/")
def main():
    transaction_list = []
    for i in range(0, 10):
        transaction_list += [{"date": "Oct 31, 2019",
                              "account": "McDonalds",
                              "amount": "-$25.00"}]
    external_list = []
    for label, number in [('External Checking', '012345654321'),
                          ('External Savings', '991235345434')]:
        external_list += [{'label': label, 'number': number}]
    internal_list = []
    for label, number in [('Friend 1', '1111111111'),
                          ('Friend 2', '2222222222')]:
        internal_list += [{'label': label, 'number': number}]
    return render_template('index.html',
                           history=transaction_list,
                           balance="$2.50",
                           name='Daniel',
                           external_accounts=external_list,
                           favorite_accounts=internal_list)


@app.route('/payment', methods=['POST'])
def payment():
    recipient = request.form['recipient']
    if recipient == 'other':
        recipient = request.form['other-recipient']
    amount = request.form['amount']
    password = request.form['password']
    print((recipient, amount, password))
    return redirect(url_for('main'))


@app.route('/deposit', methods=['POST'])
def deposit():
    account = request.form['account']
    amount = request.form['amount']
    print(account, amount)
    return redirect(url_for('main'))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format=('%(levelname)s|%(asctime)s'
                                '|%(pathname)s|%(lineno)d| %(message)s'),
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        )
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Starting flask.")
    app.run(debug=True, host='0.0.0.0')
