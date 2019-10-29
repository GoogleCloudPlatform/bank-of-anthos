from time import sleep, time
import redis
import os
import uuid
import json

ledger_redis_host = os.getenv('REDIS_ADDR_LEDGER')
ledger_redis_port = os.getenv("REDIS_PORT_LEDGER")
ledger_stream = 'ledger'#str(uuid.uuid4())

unconf_redis_host = os.getenv('REDIS_ADDR_UNCONFIRMED')
unconf_redis_port = os.getenv("REDIS_PORT_UNCONFIRMED")
unconf_stream = 'unconfirmed'#str(uuid.uuid4())

balance_dict = {}
transactions_processed = set([])

def build_balances():
    history = _ledger.xread({ledger_stream:b"0-0"})
    if len(history) == 0:
        return
    for entry in history[0][1]:
        transaction = entry[1]
        print('replaying: {}'.format(transaction))
        sender_id = transaction['send_account']
        receiver_id = transaction['recv_account']
        amount = int(transaction['amount'])
        transaction_id = transaction['transaction_id']
        balance_dict[sender_id] = balance_dict.get(sender_id, 0) - amount
        balance_dict[receiver_id] = balance_dict.get(receiver_id, 0) + amount
        transactions_processed.add(transaction_id)

def get_balance(user_id):
    return balance_dict[user_id]

def query_unconfirmed():
    result = _unconf.xread({unconf_stream:b"0-0"})
    if len(result) == 0:
        return
    for entry in result[0][1]:
        transaction = entry[1]
        redis_id = entry[0]
        sender_id = transaction['send_account']
        # sender_branch = transaction['send_branch']
        # sender_sig = transaction['send_branch_sig']
        receiver_id = transaction['recv_account']
        # receiver_branch = transaction['recv_branch']
        # receiver_sig = transaction['recv_branch_sig']
        amount = int(transaction['amount'])
        transaction_id = transaction['transaction_id']
        if transaction_id not in transactions_processed:
            print('adding: {}'.format(transaction))
            balance_dict[sender_id] = balance_dict.get(sender_id, 0) - amount
            balance_dict[receiver_id] = balance_dict.get(receiver_id, 0) + amount
            _ledger.xadd(ledger_stream, transaction)
            transactions_processed.add(transaction_id)
        else:
            print('skipping duplicate transaction')
        _unconf.xdel(unconf_stream, redis_id)


if __name__ == '__main__':
    _ledger = redis.Redis(host=ledger_redis_host, port=ledger_redis_port, db=0)
    _unconf = redis.Redis(host=unconf_redis_host, port=unconf_redis_port, db=0)
    build_balances()

    while True:
        query_unconfirmed()
        print('balances: {}'.format(balance_dict))
        sleep(5)
