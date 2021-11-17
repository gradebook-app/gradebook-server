from flask import Blueprint
from modules.auth.auth_service import AuthService
from utils.request_tools import body, genesisId
import asyncio

auth = Blueprint('auth', __name__)
auth_service = AuthService()

@auth.route('/auth/login', methods=['POST'])
@body
def login(body): 
    userId, password, school_district = (body['userId'], body['pass'], body['schoolDistrict'])
    notificationToken = body['notificationToken']
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response =  loop.run_until_complete( 
        auth_service.login(userId, password, school_district, notificationToken)
    )
    loop.close()
    return response

@auth.route('/auth/logout', methods=['POST'])
@genesisId
def logout(genesisId): 
    return auth_service.logout(genesisId)