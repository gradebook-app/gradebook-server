from flask import Flask
from rq import Queue
from worker import conn
from rq_scheduler import Scheduler
from modules.redis.grades import schedule_grade_persisting

q = Queue(connection=conn)
scheduler = Scheduler(queue=q, connection=conn)

def clear_queue():
    for job in scheduler.get_jobs(): 
        scheduler.cancel(job)

from modules.auth.auth_controller import auth as auth_blueprint 
from modules.grades.grades_controller import grades as grades_blueprint 
from modules.user.user_controller import user as user_blueprint

clear_queue()
schedule_grade_persisting()

app = Flask(__name__, instance_relative_config=False)

app.register_blueprint(auth_blueprint)
app.register_blueprint(grades_blueprint)
app.register_blueprint(user_blueprint)

@app.route('/', methods=['GET'])
def home(): 
    return "All Systems Operational."

if __name__ == "__main__": 
    app.run(port=5000, debug=True)

