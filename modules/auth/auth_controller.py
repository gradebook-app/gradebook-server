from flask import Blueprint, request
from modules.auth.auth_service import AuthService

auth = Blueprint('auth', __name__)
auth_service = AuthService()

@auth.route('/auth/login', methods=['POST'])
def login(): 
    credentials = dict(request.form)
    email, password = (credentials['email'], credentials['pass'])
    return auth_service.login(email, password)