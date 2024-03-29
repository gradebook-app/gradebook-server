from flask import Flask, request
from modules.auth.auth_controller import auth as auth_blueprint
from modules.grades.grades_controller import grades as grades_blueprint
from modules.user.user_controller import user as user_blueprint
from modules.redis.grades import clear_queue
from modules.redis.grades import schedule_grade_persisting

app = Flask(__name__, instance_relative_config=False)

clear_queue()

app.register_blueprint(auth_blueprint)
app.register_blueprint(grades_blueprint)
app.register_blueprint(user_blueprint)

schedule_grade_persisting()


@app.route("/", methods=["POST"])
def home2():
    print(request.headers["User-Agent"])
    return "All Systems Operational."


@app.route("/", methods=["GET"])
def home():
    return "All Systems Operational."


if __name__ == "__main__":
    app.run(port=5001, debug=True, host="0.0.0.0")
