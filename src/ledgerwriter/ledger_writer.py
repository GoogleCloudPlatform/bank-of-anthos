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

def build_balances():
    history = _ledger.xread({ledger_stream:b"0-0"})
    if len(history) == 0:
        return
    for entry in history[0][1]:
        transaction = entry[1]
        print('replaying: {}'.format(transaction))
        account_id = transaction['account']
        change = int(transaction['amount'])
        if transaction['kind'] == 'debit':
            change = -change
        balance_dict[account_id] = balance_dict.get(account_id, 0) + change

def get_balance(user_id):
    return balance_dict[user_id]

def query_unconfirmed():
    result = _unconf.xread({unconf_stream:b"0-0"})
    if len(result) == 0:
        return
    for entry in result[0][1]:
        transaction = entry[1]
        print('adding: {}'.format(transaction))
        redis_id = entry[0]
        account_id = transaction['account']
        change = int(transaction['amount'])
        if transaction['kind'] == 'debit':
            change = -change
        balance_dict[account_id] = balance_dict.get(account_id, 0) + change
        _ledger.xadd(ledger_stream, transaction)
        _unconf.xdel(unconf_stream, redis_id)


if __name__ == '__main__':
    _ledger = redis.Redis(host=ledger_redis_host, port=ledger_redis_port, db=0)
    _unconf = redis.Redis(host=unconf_redis_host, port=unconf_redis_port, db=0)
    build_balances()

    while True:
        query_unconfirmed()
        print('balances: {}'.format(balance_dict))
        sleep(5)
