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



if __name__ == '__main__':
    print('host: {} port: {}'.format(redis_host, redis_port))

    r = redis.Redis(host=redis_host, port=redis_port, db=0)

    while True:
        add_transaction('dan', 'sanche', 10)
        print('added transaction to stream')
        sleep(5)
