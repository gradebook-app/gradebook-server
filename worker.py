import sys
from time import sleep
import redis
from rq import Worker, Queue, Connection
from rq.job import Job
from rq_scheduler import Scheduler
from decouple import config

listen = ["default", "low"]

try:
    queue_idx = sys.argv.index("-q")
    queues = sys.argv[queue_idx + 1].strip().split(",")
    if len(queues):
        listen = queues
except ValueError:
    print(f"Queue (-q) flag not specified, listening for jobs on queues: {listen}")
except IndexError:
    print(
        f"Queue (-q) flag specified without a value, listening for jobs on queues: {listen}"
    )

redis_url = config("REDIS_URL", "redis://localhost:6379")

conn = redis.from_url(redis_url)
queue = Queue(
    connection=conn,
)
scheduler = Scheduler(queue=queue, connection=conn)


def black_hole(job: Job, *_exc_info):
    print("Job Cancelled due to exception: ", job.id, _exc_info)
    job.cancel()
    job.cleanup(60 * 60 * 24 * 2)
    return False


def exception_handler():
    print("exception")


def bootstrap():
    print("Redis Connection URI: ", redis_url)
    try:
        with Connection(conn):
            worker = Worker(
                map(Queue, listen),
                exception_handlers=[black_hole],
                disable_default_exception_handler=True,
            )
            print(f"Working @ {worker.pid}")
            worker.work()

    except redis.exceptions.ConnectionError as _:
        retry_interval = 5
        print(
            f"Redis Connection Failed @{redis_url}, attempting retry in {retry_interval} seconds..."
        )
        sleep(retry_interval)
        bootstrap()


if __name__ == "__main__":
    bootstrap()
