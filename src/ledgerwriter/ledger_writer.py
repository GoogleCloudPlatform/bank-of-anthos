from time import sleep
import redis
import os
import uuid

if __name__ == '__main__':
    redis_host = os.getenv('REDIS_ADDR')
    redis_port = os.getenv("REDIS_PORT")
    stream_name = str(uuid.uuid4())

    print('host: {} port: {}'.format(redis_host, redis_port))

    r = redis.Redis(host=redis_host, port=redis_port, db=0)

    i=0
    while True:
        r.xadd(stream_name, {'num':i})
        out = r.xread({stream_name:b"0-0"})
        print(out)
        sleep(5)
        i+=1
