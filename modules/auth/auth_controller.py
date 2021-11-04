from flask import Blueprint
from modules.auth.auth_service import AuthService
from utils.request_tools import body, genesisId

auth = Blueprint('auth', __name__)
auth_service = AuthService()

@auth.route('/auth/login', methods=['POST'])
@body
def login(body): 
    userId, password, school_district = (body['userId'], body['pass'], body['schoolDistrict'])
    notificationToken = body['notificationToken']
    return auth_service.login(userId, password, school_district, notificationToken)

@auth.route('/auth/logout', methods=['POST'])
@genesisId
def logout(genesisId): 
    return auth_service.logout(genesisId)