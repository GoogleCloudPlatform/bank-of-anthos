from time import sleep, time
import redis
import os
import uuid
import json

redis_host = os.getenv('REDIS_ADDR')
redis_port = os.getenv("REDIS_PORT")
stream_name = str(uuid.uuid4())

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

def get_balance(user_id):
    balance = 0
    history = r.xread({stream_name:b"0-0"})
    for entry in history[0][1]:
        transaction = entry[1]
        print(transaction)
        if transaction['account'] == user_id:
            if transaction['kind'] == 'credit':
                balance += int(transaction['amount'])
            elif transaction['kind'] == 'debit':
                balance -= int(transaction['amount'])
    return balance

if __name__ == '__main__':
    print('host: {} port: {}'.format(redis_host, redis_port))

    r = redis.Redis(host=redis_host, port=redis_port, db=0)

    while True:
        add_transaction('dan', 'sanche', 10)
        b1 = get_balance('dan')
        b2 = get_balance('sanche')
        print('balances: dan={}, sanche={}'.format(b1, b2))
        sleep(5)
