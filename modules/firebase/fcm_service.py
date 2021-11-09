from pyfcm import FCMNotification
from config.config import config

class FCMService: 
    def __init__(self): 
        self.push_service = FCMNotification(api_key=config['fcm']['key'])

    def send_message(self, token, title, message): 
        self.push_service.notify_single_device(
            registration_id=token,
            message_title=title,
            message_body=message
        )
        