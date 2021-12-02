from worker import queue as q, scheduler
from modules.grades.grades_service import GradesService

def clear_queue():
    for job in scheduler.get_jobs(): 
        scheduler.cancel(job)

def query_grades(): 
    grades_service = GradesService()
    q.enqueue_call(func=grades_service.query_grades, args=(0, ))

def enqueue_processes(): 
    scheduler.cron(
        repeat=False,
        cron_string="*/5 * * * *",
        func=query_grades,
        id="query grades",
        args=(),
        queue_name="default",
        use_local_timezone=False,
    )

def schedule_grade_persisting(): 
    clear_queue()
    enqueue_processes()