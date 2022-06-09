from time import sleep
import redis
from rq import Worker, Queue, Connection
from rq_scheduler import Scheduler
from decouple import config

listen = ['default', 'low']

redis_url = config('REDIS_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)
queue = Queue(connection=conn, )
scheduler = Scheduler(queue=queue, connection=conn)

def exception_handler(): 
    print("exception")

def bootstrap(): 
    print("Redis Connection URI: ", redis_url)
    try: 
        with Connection(conn):
            worker = Worker(map(Queue, listen))
            worker.work()

    except redis.exceptions.ConnectionError as _: 
        retry_interval = 5
        print(f"Redis Connection Failed @{redis_url}, attempting retry in {retry_interval} seconds...")
        sleep(retry_interval)
        bootstrap()

if __name__ == '__main__':
    bootstrap()