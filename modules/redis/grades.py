from worker import queue as q, scheduler
from modules.grades.grades_service import GradesService

def clear_queue():
    for job in scheduler.get_jobs(): 
        scheduler.cancel(job)

def query_grades(): 
    jobs = q.get_jobs()
    if len(jobs):
        print("Skipping Persisting, Queue Busy") 
        return 
    grades_service = GradesService()
    q.enqueue_call(func=grades_service.query_grades, args=(0, ))

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