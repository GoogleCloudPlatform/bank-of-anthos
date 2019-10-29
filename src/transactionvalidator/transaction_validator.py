from time import sleep, time
import redis
import os
import uuid
import json

unconf_host = os.getenv('UNCONF_ADDR')
unconf_port = os.getenv('UNCONF_PORT')
stream_name = os.getenv("UNCONF_STREAM")

key_path = os.getenv("KEY_PATH")
def add_transaction(from_id, to_id, amount):
    transaction_id = str(uuid.uuid4())
    timestamp = time()
    trans_obj = {'send_account':from_id,
                 'send_branch':'1234',
                 'send_branch_sig':'',
                 'recv_account':to_id,
                 'recv_branch':'1234',
                 'recv_branch_sig':'',
                 'amount':amount,
                 'time':timestamp,
                 'transaction_id':transaction_id
                }
    r.xadd(stream_name, trans_obj)
    print('added transaction: {}'.format(trans_obj))

if __name__ == '__main__':
    print('host: {} port: {}'.format(unconf_host, unconf_port))

    r = redis.Redis(host=unconf_host, port=unconf_port, db=0)

    while True:
        add_transaction('dan', 'sanche', 10)
        sleep(10)
