from flask import Blueprint
from utils.request_tools import body, genesisId, query
from modules.user.user_service import UserService

user = Blueprint('user', __name__)

user_service = UserService()

@user.route("/user/account", methods=["GET"])
@genesisId
def get_user_account(genesisId): 
    return user_service.get_user_account(genesisId)

@user.route('/user/setNotificationToken', methods=['POST'])
@body
@genesisId
def set_notification_token(body, genesisId): 
    token = body["notificationToken"]
    return user_service.set_notification_token(token, genesisId)

@user.route("/user/schedule", methods=['GET'])
@genesisId
@query
def get_user_schedule(genesisId, query): 
    return user_service.get_schedule(genesisId, query)