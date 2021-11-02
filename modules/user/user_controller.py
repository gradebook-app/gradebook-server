from flask import Blueprint
from utils.request_tools import body, genesisId
from modules.user.user_service import UserService

user = Blueprint('user', __name__)

user_service = UserService()

@user.route('/user/setNotificationToken', methods=['POST'])
@body
@genesisId
def set_notification_token(body, genesisId): 
    token = body["notificationToken"]
    return user_service.set_notification_token(token, genesisId)
