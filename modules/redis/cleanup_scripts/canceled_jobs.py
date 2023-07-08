import redis
from decouple import config
from rq import Queue
import concurrent.futures
import threading

redis_url = config("REDIS_URL", "redis://localhost:6379")
conn = redis.from_url(redis_url)
queue = Queue("default", connection=conn) # change queue to `default` if you want to clean up keys in `default`

canceled_job_ids = queue.canceled_job_registry.get_job_ids()
print(f"Canceled Jobs: {len(canceled_job_ids)}")
max_workers = 15

pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

def clean_up_jobs(job_ids): 
    print("Thread ID: ", threading.get_native_id())
    for job_id in job_ids: 
        job = queue.fetch_job(job_id)
        if job and job.get_ttl() is None and (job.retries_left is None or job.retries_left < 1): 
            print(f"Preparing Job with ID {job_id} and Status {job._status} for Clean Up")
            job.cleanup(60 * 60 * 24 * 2) # 2 days
        else: 
            print(f"Job with ID {job_id} doesn't exist or has TTL or Retries")
            queue.canceled_job_registry.remove(job_id)
    
remaining_jobs = len(canceled_job_ids) % max_workers
equal_jobs = len(canceled_job_ids) // max_workers

for i in range(max_workers): 
    pool.submit(
        clean_up_jobs, 
        canceled_job_ids[equal_jobs*i:equal_jobs*(i+1) if i != max_workers - 1 else -1]
    )
pool.shutdown(wait=True)

print(f"Prepared All Jobs for Clean Up.")