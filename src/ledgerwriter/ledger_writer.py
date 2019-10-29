from time import sleep, time
import redis
import os
import uuid
import json

branch_id = os.getenv("BRANCH_ID")

ledger_host = os.getenv('LEDGER_ADDR')
ledger_port = os.getenv("LEDGER_PORT")
ledger_stream = os.getenv('LEDGER_STREAM')

unconf_host = os.getenv('UNCONF_ADDR')
unconf_port = os.getenv("UNCONF_PORT")
unconf_stream = os.getenv('UNCONF_STREAM')

balance_dict = {}
transactions_processed = set([])

def _local_cache_transaction(transaction):
    sender_id = transaction['send_account']
    sender_branch = transaction['send_branch']
    receiver_id = transaction['recv_account']
    receiver_branch = transaction['recv_branch']
    amount = int(transaction['amount'])
    transaction_id = transaction['transaction_id']
    if sender_branch == branch_id:
        balance_dict[sender_id] = balance_dict.get(sender_id, 0) - amount
    if receiver_branch == branch_id:
        balance_dict[receiver_id] = balance_dict.get(receiver_id, 0) + amount
    transactions_processed.add(transaction_id)

def build_balances():
    history = _ledger.xread({ledger_stream:b"0-0"})
    if len(history) == 0:
        return
    for entry in history[0][1]:
        transaction = entry[1]
        print('replaying: {}'.format(transaction))
        _local_cache_transaction(transaction)

def get_balance(user_id):
    return balance_dict[user_id]

def query_unconfirmed():
    result = _unconf.xread({unconf_stream:b"0-0"})
    if len(result) == 0:
        return
    for entry in result[0][1]:
        transaction = entry[1]
        redis_id = entry[0]
        if transaction['transaction_id'] in transactions_processed:
            print('error: skipping duplicate transaction')
        elif not (transaction['send_branch'] == branch_id or 
                transaction['recv_branch'] == branch_id):
            print('error: skipping transaction with no matching branch')
        else:
            print('adding: {}'.format(transaction))
            _ledger.xadd(ledger_stream, transaction)
            _local_cache_transaction(transaction)
        _unconf.xdel(unconf_stream, redis_id)


if __name__ == '__main__':
    _ledger = redis.Redis(host=ledger_host, port=ledger_port, db=0)
    _unconf = redis.Redis(host=unconf_host, port=unconf_port, db=0)
    build_balances()

    while True:
        query_unconfirmed()
        print('balances: {}'.format(balance_dict))
        sleep(5)
