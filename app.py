from flask import Flask
from modules.auth.auth_controller import auth as auth_blueprint 
from modules.grades.grades_controller import grades as grades_blueprint 
from modules.user.user_controller import user as user_blueprint
from modules.redis.grades import clear_queue

app = Flask(__name__, instance_relative_config=False)

clear_queue()

app.register_blueprint(auth_blueprint)
app.register_blueprint(grades_blueprint)
app.register_blueprint(user_blueprint)

@app.route('/', methods=['GET'])
def home(): 
    return "All Systems Operational."

if __name__ == "__main__": 
    app.run(port=5000, debug=True)

