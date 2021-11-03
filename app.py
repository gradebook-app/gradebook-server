from flask import Flask
from modules.grades.grades_service import GradesService
from rq import Queue
from worker import conn
from rq_scheduler import Scheduler

from modules.auth.auth_controller import auth as auth_blueprint 
from modules.grades.grades_controller import grades as grades_blueprint 
from modules.user.user_controller import user as user_blueprint

q = Queue('default', connection=conn)
scheduler = Scheduler(queue=q, connection=conn)

def clear_queue():
    for job in scheduler.get_jobs(): 
        scheduler.cancel(job)

def query_grades(): 
    grades_service = GradesService()
    q.enqueue_call(func=grades_service.query_grades, args=(0, ))

def enqueue_processes(): 
    scheduler.cron(
        cron_string="*/5 * * * *",
        func=query_grades,
        id="query grades",
        args=(),
        queue_name="default",
        use_local_timezone=False,
    )

app = Flask(__name__, instance_relative_config=False)

app.register_blueprint(auth_blueprint)
app.register_blueprint(grades_blueprint)
app.register_blueprint(user_blueprint)

clear_queue()
query_grades()

@app.route('/', methods=['GET'])
def home(): 
    return "All Systems Operational."

if __name__ == "__main__": 
    app.run(port=5000, debug=True)

