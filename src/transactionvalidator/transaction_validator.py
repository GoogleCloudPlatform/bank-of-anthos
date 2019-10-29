from time import sleep, time
import redis
import os
import uuid
import json

redis_host = os.getenv('REDIS_ADDR')
redis_port = os.getenv("REDIS_PORT")
stream_name = 'unconfirmed' #str(uuid.uuid4())

def add_transaction(from_id, to_id, amount):
    transaction_id = str(uuid.uuid4())
    timestamp = time()
    trans_obj = {'send_account':from_id,
                 'send_branch':'0',
                 'send_branch_sig':'',
                 'recv_account':to_id,
                 'recv_branch':'0',
                 'recv_branch_sig':'',
                 'amount':amount,
                 'time':timestamp,
                 'transaction_id':transaction_id
                }
    r.xadd(stream_name, trans_obj)



if __name__ == '__main__':
    print('host: {} port: {}'.format(redis_host, redis_port))

    r = redis.Redis(host=redis_host, port=redis_port, db=0)

    while True:
        add_transaction('dan', 'sanche', 10)
        print('added transaction to stream')
        sleep(10)
