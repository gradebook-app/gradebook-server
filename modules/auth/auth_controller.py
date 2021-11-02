from flask import Blueprint
from modules.auth.auth_service import AuthService
from utils.request_tools import body

auth = Blueprint('auth', __name__)
auth_service = AuthService()

@auth.route('/auth/login', methods=['POST'])
@body
def login(body): 
    userId, password, school_district = (body['userId'], body['pass'], body['schoolDistrict'])
    return auth_service.login(userId, password, school_district)
