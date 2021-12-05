import os
from time import sleep
import redis
from rq import Worker, Queue, Connection
from rq_scheduler import Scheduler

listen = ['default']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)
queue = Queue(connection=conn)
scheduler = Scheduler(queue=queue, connection=conn)

def exception_handler(): 
    print("exception")

def bootstrap(): 
    try: 
        with Connection(conn):
            worker = Worker(map(Queue, listen))
            worker.work()

    except redis.exceptions.ConnectionError as _: 
        retry_interval = 5
        print(f"Redis Connection Failed, attempting retry in {retry_interval} seconds...")
        sleep(retry_interval)
        bootstrap()

if __name__ == '__main__':
    bootstrap()