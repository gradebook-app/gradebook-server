from flask import Flask

from modules.auth.auth_controller import auth as auth_blueprint 
from modules.grades.grades_controller import grades as grades_blueprint 

app = Flask(__name__)

app.register_blueprint(auth_blueprint)
app.register_blueprint(grades_blueprint)

@app.route('/', methods=['GET'])
def home(): 
    return "All Systems Operational."

if __name__ == "__main__": 
    app.run(port=5000, debug=True)
