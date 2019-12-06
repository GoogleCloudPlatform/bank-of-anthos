import logging
import os
import threading
from collections import defaultdict

from flask import Flask, jsonify, request

import redis


app = Flask(__name__)

ledger_host = os.getenv('LEDGER_ADDR')
ledger_port = os.getenv("LEDGER_PORT")
ledger_stream = os.getenv('LEDGER_STREAM')

_local_routing_num = os.getenv('LOCAL_ROUTING_NUM')

balance_dict = defaultdict(int)


@app.route('/healthz', methods=['GET'])
def readiness():
    return 'ok', 200


@app.route('/get_balance', methods=['GET'])
def get_balance():
    account_id = request.args.get('account_id')
    if account_id is None:
        return jsonify({'error': 'account %s not found' % account_id}), 500
    balance = balance_dict[account_id]
    return jsonify({'balance': balance}), 201


def _process_transaction(transaction):
    sender_acct = transaction['from_account_num']
    sender_route = transaction['from_routing_num']
    receiver_acct = transaction['to_account_num']
    receiver_route = transaction['to_routing_num']
    amount = int(transaction['amount'])
    if sender_route == _local_routing_num:
        balance_dict[sender_acct] -= amount
    if receiver_route == _local_routing_num:
        balance_dict[receiver_acct] += amount


def _query_transactions(last_transaction_id=b'0-0', block=True):
    if block:
        # block until new transactions arrive
        block_time = 0
    else:
        # don't block
        block_time = None

    new_set = _ledger.xread({ledger_stream: last_transaction_id},
                            block=block_time)
    if len(new_set) > 0:
        for entry in new_set[0][1]:
            last_transaction_id = entry[0]
            transaction = entry[1]
            logging.info('processing transaction: {}'.format(transaction))
            _process_transaction(transaction)
    return last_transaction_id


def transaction_listener(last_transaction_id):
    while True:
        last_transaction_id = _query_transactions(
            last_transaction_id=last_transaction_id,
            block=True
        )


if __name__ == '__main__':
    for v in ['PORT', 'LEDGER_ADDR', 'LEDGER_STREAM', 'LEDGER_PORT',
              'LOCAL_ROUTING_NUM']:
        if os.environ.get(v) is None:
            print("error: {} environment variable not set".format(v))
            exit(1)
    _ledger = redis.Redis(host=ledger_host, port=ledger_port, db=0)

    logging.info('restoring balances...')
    last_transaction_id = _query_transactions(block=False)

    logging.info('starting transaction listener thread...')
    thread = threading.Thread(target=transaction_listener,
                              args=[last_transaction_id])
    thread.daemon = True
    thread.start()

    logging.info("starting flask...")
    app.run(debug=False, port=os.environ.get('PORT'), host='0.0.0.0')
