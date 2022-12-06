from time import sleep
import redis
from rq import Worker, Queue, Connection
from rq_scheduler import Scheduler
from decouple import config

listen = ['default']

redis_url = config('REDIS_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)
queue = Queue(connection=conn, )
scheduler = Scheduler(queue=queue, connection=conn)

def black_hole(job, *_exc_info):
    print("Job Cancelled due to exception: ", job.id)
    job.cancel()
    return False

def exception_handler(): 
    print("exception")

def bootstrap(): 
    print("Redis Connection URI: ", redis_url)
    try: 
        with Connection(conn):
            worker = Worker(map(Queue, listen), exception_handlers=[ black_hole ], disable_default_exception_handler=True)
            print(f"Working @ {worker.pid}")
            worker.work()

    except redis.exceptions.ConnectionError as _: 
        retry_interval = 5
        print(f"Redis Connection Failed @{redis_url}, attempting retry in {retry_interval} seconds...")
        sleep(retry_interval)
        bootstrap()

if __name__ == '__main__':
    bootstrap()