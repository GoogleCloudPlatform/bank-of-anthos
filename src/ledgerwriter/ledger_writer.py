from time import sleep, time
import redis
import os
import uuid
import json

redis_host = os.getenv('REDIS_ADDR')
redis_port = os.getenv("REDIS_PORT")
stream_name = 'confirmed'#str(uuid.uuid4())

balance_dict = {}

def add_transaction(from_id, to_id, amount):
    transaction_id = str(uuid.uuid4())
    timestamp = time()
    debit_obj = {'kind':'debit',
                 'account':from_id,
                 'amount':amount,
                 'time':timestamp,
                 'transaction_id':transaction_id}
    credit_obj = {'kind':'credit',
                 'account':to_id,
                 'amount':amount,
                 'time':timestamp,
                 'transaction_id':transaction_id}
    r.xadd(stream_name, debit_obj)
    r.xadd(stream_name, credit_obj)
    balance_dict[from_id] = balance_dict.get(from_id, 0) - amount
    balance_dict[to_id] = balance_dict.get(to_id, 0) + amount

def build_balances():
    history = r.xread({stream_name:b"0-0"})
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

if __name__ == '__main__':
    print('host: {} port: {}'.format(redis_host, redis_port))

    r = redis.Redis(host=redis_host, port=redis_port, db=0)
    build_balances()

    while True:
        add_transaction('dan', 'sanche', 10)
        b1 = get_balance('dan')
        b2 = get_balance('sanche')
        print('balances: {}'.format(balance_dict))
        sleep(5)
