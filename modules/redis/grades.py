from worker import conn, scheduler
from rq import Queue
from modules.grades.grades_service import GradesService

default_queue = Queue('default', connection=conn)

def clear_queue():
    for job in scheduler.get_jobs(): 
        scheduler.cancel(job)

def query_grades(): 
    jobs = default_queue.get_jobs()
    if len(jobs):
        print("Skipping Persisting, Queue Busy", print(jobs)) 
        return 
    grades_service = GradesService()
    default_queue.enqueue_call(func=grades_service.query_grades, args=(0, ))

def enqueue_processes(): 
    scheduler.cron(
        cron_string="*/5 * * * *",
        func=query_grades,
        id="query_grades_scheduler",
        args=(),
        queue_name="default",
        use_local_timezone=False,
    )

def schedule_grade_persisting():
    clear_queue()
    enqueue_processes()